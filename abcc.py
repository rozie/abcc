#!/usr/bin/python
# -*- coding: utf-8 -*-

import argparse
import logging
import ping
import yaml
from subprocess import call


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_ip_score(ip, loss_mult, lag_mult, count):
    logger.debug("IP {} loss_mult {} lag_mult {} count {}"
                 .format(ip, loss_mult, lag_mult, count))

    result = ping.quiet_ping(ip, 2, count)
    (loss, lag) = (result[0], result[2])
    logger.debug("loss {} lag {}".format(loss, lag))
    if not lag:
        lag = 1000
        logger.warning("IP {} is unreachable".format(ip))
    score = loss_mult*loss + lag_mult*lag
    logger.debug("Returning score {} for IP {}".format(score, ip))
    return score


def set_routing_ip(ip, interface, gateway):
    logger.debug("Setting routing for ip {} through gateway {} on interface {}"
                 .format(ip, gateway, interface))
    result = call(["./plugins/generic_route_set.sh", ip, gateway])
    logger.debug("Exit code is {}".format(result))
    return result


def del_routing_ip(ip, interface, gateway):
    logger.debug("Deleting routing for ip {} through gateway {} on interface {}"
                 .format(ip, gateway, interface))
    result = call(["./plugins/generic_route_del.sh", ip, gateway])
    logger.debug("Exit code is {}".format(result))
    return result


def get_route_score(route, interface, data):
    logger.debug("Getting score for route {} interface {}".
                 format(route, interface))
    route_sum = 0
    weight_sum = 0
    lag_mult = data['routes'][route].get('lag_mult', 1)
    loss_mult = data['routes'][route].get('loss_mult', 10)
    gateway = data['interfaces'][interface].get('gateway')
    for ip in data['routes'][route].get('IPs'):
        if not set_routing_ip(ip, interface, gateway):
            count = data['routes'][route]['IPs'][ip].get('count', 10)
            ip_weight = data['routes'][route]['IPs'][ip].get('weight', 1)
            logger.debug("Weight for IP {} is {}".format(ip, ip_weight))
            ip_score = get_ip_score(ip, loss_mult, lag_mult, count)
            route_sum += ip_score*ip_weight
            weight_sum += ip_weight
            if del_routing_ip(ip, interface, gateway):
                logger.warning("Failed to remove routing for IP {} via {}\
 on interface {}".format(ip, gateway, interface))
        else:
            logger.warning("Failed to set routing for IP {} via {}\
 on interface {}".format(ip, gateway, interface))
        logger.debug("Route sum is now {}".format(route_sum))
    if weight_sum == 0:
        weight_sum = 1
    route_score = float(route_sum/weight_sum)
    logger.debug("Route sum is {}, route score is {}"
                 .format(route_sum, route_score))
    return route_score


def main():
    args = parse_arguments()
    try:
        with open(args.config, "r") as config:
            data = yaml.load(config)
    except:
        logger.error("Couldn't read config file {}".format(config))

    for interface in data.get('interfaces'):
        logger.debug("Testing interface {}".format(interface))
        for route in data['interfaces'][interface].get('routes'):
            logger.debug("Testing route {} on interface {}".format(route,
                         interface))
            score = get_route_score(route, interface, data)
            logger.info("Route {} got score {} on interface {}"
                        .format(route, score, interface))


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='abcc - Automatic Best Connection Chooser')

    parser.add_argument(
        '--dry-run', required=False,
        default=False,
        help="Just print data, don't change anything")
    parser.add_argument(
        '--verbose', required=False,
        default=True,
        help="Provide verbose output")
    parser.add_argument(
        '--config', required=False,
        default="example.yaml",
        help="Configuration file"
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':
    main()
