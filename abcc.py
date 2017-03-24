#!/usr/bin/python

import argparse
import ping
import yaml


def get_ip_score(ip, loss_mult, lag_mult, count):
    result = ping.quiet_ping(ip, 2, count)
    (loss, lag) = (result[0], result[2])
#    print loss, lag, loss_mult, lag_mult
    if not lag:
        lag = 1000
    score = loss_mult*loss + lag_mult*lag
    print "loss", loss, "lag", lag
    return score


def get_route_score(route):
    route_sum = 0
    loss_mult = route.get('loss_mult', 10)
    lag_mult = route.get('lag_mult', 1)
    for ip in route.get('IPs'):
        weight_sum = 0
        count = route['IPs'][ip].get('count', 10)
        ip_weight = route['IPs'][ip].get('weight', 1)
        ip_score = get_ip_score(ip, loss_mult, lag_mult, count)
        route_sum += ip_score*ip_weight
        weight_sum += ip_weight
    route_score = float(route_sum/weight_sum)
    print route_sum, route_score
    return route_score


def main():
    args = parse_arguments()

    try:
        with open(args.config, "r") as config:
            data = yaml.load(config)
    except:
        print "Bug!"

    for route in data.get('routes'):
        print route, get_route_score(data['routes'][route])


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
