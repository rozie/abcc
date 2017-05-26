#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import re
from subprocess import call, check_output

import ping
import yaml

logger = logging.getLogger(__name__)


def get_ip_score(ip, loss_mult, lag_mult, count):
    logger.debug("IP %s loss_mult %s lag_mult %s count %s", ip, loss_mult,
                 lag_mult, count)

    result = ping.quiet_ping(ip, 2, count)
    (loss, lag) = (result[0], result[2])
    logger.debug("loss %s lag %s", loss, lag)
    if not lag:
        lag = 1000
        logger.warning("IP %s is unreachable", ip)
    score = loss_mult * loss + lag_mult * lag
    logger.debug("Returning score %s for IP %s", score, ip)
    return score


def set_routing_ip(ip, interface, gateway):
    logger.debug("Setting routing for ip %s via gateway %s on interface %s",
                 ip, gateway, interface)
    result = call(["./plugins/generic_route_set.sh", ip, gateway])
    logger.debug("Exit code is %s", result)
    return result


def del_routing_ip(ip, interface, gateway):
    logger.debug("Deleting routing for ip %s via gateway %s on interface %s",
                 ip, gateway, interface)
    result = call(["./plugins/generic_route_del.sh", ip, gateway])
    logger.debug("Exit code is %s", result)
    return result


def get_route_score(route, interface, data):
    logger.debug("Getting score for route %s interface %s", route, interface)
    route_sum = 0
    weight_sum = 0
    lag_mult = data['routes'][route].get('lag_mult', 1)
    loss_mult = data['routes'][route].get('loss_mult', 10)
    gateway = data['interfaces'][interface].get('gateway')
    for ip in data['routes'][route].get('IPs'):
        if not set_routing_ip(ip, interface, gateway):
            count = data['routes'][route]['IPs'][ip].get('count', 10)
            ip_weight = data['routes'][route]['IPs'][ip].get('weight', 1)
            logger.debug("Weight for IP %s is %s", ip, ip_weight)
            ip_score = get_ip_score(ip, loss_mult, lag_mult, count)
            route_sum += ip_score * ip_weight
            weight_sum += ip_weight
            if del_routing_ip(ip, interface, gateway):
                logger.error("Failed to remove routing for IP %s via %s\
 on interface %s", ip, gateway, interface)
        else:
            route_sum += 1000
            logger.error("Failed to set routing for IP %s via %s\
 on interface %s", ip, gateway, interface)
        logger.debug("Route sum is now %s", route_sum)
    if weight_sum == 0:
        weight_sum = 1
    route_score = float(route_sum / weight_sum)
    logger.debug("Route sum is %s, route score is %s", route_sum, route_score)
    return route_score


def get_best_interfaces_for_routes(data, scores):
    logger.debug("Checking best interfaces")
    best = {}
    best_score = {}
    for interface in data.get('interfaces'):
        for route in data['interfaces'][interface].get('routes'):
            score = scores[interface][route]
            if not best.get(route) or score < best_score.get(route):
                best[route] = interface
                best_score[route] = score
                logger.debug("New best interface %s for route %s found. The \
score is %s", interface, route, score)
    return best


def get_current_routing_table():
    result = check_output(["ip", "route"])
    logger.debug("Current routing table: %s", result)
    return result


def get_current_interfaces_for_routes(data):
    # read_routing_table
    routing = {}
    table = get_current_routing_table().splitlines()
    for line in table:
        match = re.match(r"(\S+)\s+via\s+(\S+)\s+dev\s+(\S+)", line)
        if match:
            route = match.group(1)
            iface = match.group(3)
            routing[route] = iface
            logger.debug("Found route %s via iface %s", route, iface)
            if route in routing and routing.get(route) != iface:
                logger.error("Route %s found on iface %s, but already known",
                             route, iface)
    logger.debug("Routing is %s", routing)
    return routing


def compare_scores(scores, routing, best, data):
    for route in data.get('routes'):
        logger.debug("Checking route %s", route)
        best_iface = best.get(route)
        curr_iface = routing.get(route)
        if best_iface != curr_iface:
            logger.debug("Best iface %s is not current %s", best_iface,
                         curr_iface)
            switch_cost = data.get(route).get("switch_cost", 100)
            logger.debug("Switch cost for route %s is %s", route, switch_cost)
            curr_score = scores.get(curr_iface).get(route)
            best_score = scores.get(best_iface).get(route)
            logger.debug("Current score %s, best score %s", curr_score,
                         best_score)
            if curr_score and best_score:
                if best_score + switch_cost < curr_score:
                    logger.info("Switching routing for %s to iface %s", route,
                                best_iface)
                else:
                    logger.info("Iface %s score %s better than iface %s score\
for route %s but switching cost is too high", best_iface, best_score,
                                curr_iface, curr_score, route)
            else:
                logger.warning("Cannot compare scores - current or best scores\
is not available")
        else:
            logger.debug("Best iface %s is the same as %s", best_iface,
                         curr_iface)


def main():
    args = parse_arguments()

    # set verbosity
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # load config file
    try:
        with open(args.config, "r") as config:
            data = yaml.load(config)
    except:
        logger.error("Couldn't read config file %s", config)

    scores = {}
    # get score for all routes on all interfaces
    for interface in data.get('interfaces'):
        logger.debug("Testing interface %s", interface)
        scores[interface] = {}
        for route in data['interfaces'][interface].get('routes'):
            logger.debug("Testing route %s on interface %s", route, interface)
            score = get_route_score(route, interface, data)
            logger.info("Route %s got score %s on interface %s", route, score,
                        interface)
            scores[interface][route] = score

    # get_current_interfaces_for_routes()
    routing = get_current_interfaces_for_routes(data)
    print routing

    # choose_best_interface_for_route()
    best = get_best_interfaces_for_routes(data, scores)
    print best

    # compare current with best
    compare_scores(scores, routing, best, data)

    # set_routing_for_route()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='abcc - Automatic Best Connection Chooser')

    parser.add_argument(
        '-d', '--dry-run', required=False,
        default=False, action='store_true',
        help="Just print data, don't change anything")
    parser.add_argument(
        '-v', '--verbose', required=False,
        default=False, action='store_true',
        help="Provide verbose output")
    parser.add_argument(
        '-c', '--config', required=False,
        default="example.yaml",
        help="Configuration file"
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
