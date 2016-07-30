from __future__ import print_function
from __future__ import absolute_import
from termcolor import colored
from six.moves import input
import os
import fedmsg
import argparse
import calendar
import fedmsg.meta
import stats
import output
from parseGroup import GroupParser


def interactive_input(args):
    stats.values['user'] = str(input("FAS Username (required) \t: ")).lower()
    stats.values['delta'] = 604800 * int(input("Number of weeks (default : 1)\t: "))
    stats.weeks = int(args.weeks)
    stats.category = str(input("Enter category (default : None)\t: ")).lower() or ''
    stats.start = str(input("Start Time (MM/DD/YYYY) \t: ")) or ''
    stats.end = str(input("Start Time (MM/DD/YYYY) \t: ")) or ''
    output.mode = str(input("Output Type (default : text) \t: ")).lower() or 'text'
    output.filename = str(input("Filename [default : $username] \t: ")).lower() or \
        stats.values['user']


def assign_values(args):
    stats.values['user'] = str(args.user).lower()
    stats.values['delta'] = int(args.weeks) * 604800
    stats.category = args.category.lower()
    stats.start = args.start
    stats.end = args.end
    stats.weeks = int(args.weeks)
    stats.group = args.group
    stats.log = args.log
    output.mode = args.mode.lower()
    output.filename = args.user.lower()


def add_arguments(parser):
    parser.add_argument('--category', '-c', help="Sub Category", default='')
    parser.add_argument('--end', '-e', help="End Date", default='')
    parser.add_argument('--group', '-g', help="FAS Group", default='')
    parser.add_argument('--interactive', '-i', help="Enable interactive mode",
                            action='store_true')
    parser.add_argument('--log', '-l', help="Enable full log reporting",
                            action='store_true')
    parser.add_argument('--mode', '-m', help="Type of Output", default='text')
    parser.add_argument('--output', '-o', help="Output name", default='stats')
    parser.add_argument('--start', '-s', help="Start Date", default='')
    parser.add_argument('--user', '-u', help='FAS username')
    parser.add_argument('--weeks', '-w', help='Time in weeks', default=1)


def generator(args, mode, user):
    if mode=='group':
        args.user = user
        stats.values['user'] = user

    # Else, use the argparse values. No arguments is handled by argparse.
    assign_values(args)
    # For png and SVG, we need a drawable object to be called
    if output.mode in ['png', 'svg', 'csv'] or not stats.log and output.mode == 'text':
    # Draw object for the above mentioned categories.
        draw_obj = stats.return_categories()

        # To handle user with no activity; TO-DO -> Make this a function
        if len(draw_obj) == 0:
            print (colored("[!] ", 'red') + 'No activity found for user ' +
            args.user)
            return 1

        # Generate the output graph objects required for calling generate_graph
        output.generate_graph(draw_obj, "Topic distribution of " +
                                        stats.values['user'], None, 'bar')
        draw_obj2 = stats.return_subcategories(stats.category)
        interactions = stats.return_interactions(draw_obj2)

        # Check if a category input was given and generate category graph
        if stats.category != '':
            output.generate_graph(
                draw_obj2,
                "Category: " +
                stats.category +
                "\nUser: " +
                args.user,
                stats.category,
                'pie')

        # Check if the sub-sub-category exists and generate it's graph
        if None not in list(interactions.keys()):
            for keys in interactions:
                i_count += 1
                output.generate_graph(
                    interactions[keys],
                    "Interaction with " +
                    str(keys) +
                    "\nCategory:  " +
                    stats.category.capitalize(),
                    stats.category +
                    "_" +
                    keys,
                    'bar')

    # If not image, check if the input matches any of the text based inputs
    elif output.mode in ['json', 'text', 'markdown', 'gource']:
        draw_obj = stats.return_json()

        # To handle user with no activity
        if draw_obj['total'] == 0:
            print (colored("[!] ", 'red') + 'No activity found for user ' +
                   str(args.user))
            return 1
        output.generate_graph(draw_obj, args.user)
        stats.unicode_json = {}


def main():
    # fedmsg config
    config = fedmsg.config.load_config()
    fedmsg.meta.make_processors(**config)

    # Initializing to None to prevent errors while generating multiple reports
    stats.unicode_json = {}
    i_count = 0
    group_userlist = list()

    # Argument Parser initialization
    parser = argparse.ArgumentParser(description='Fedora Statistics Gatherer')
    add_arguments(parser)
    args = parser.parse_args()

    if args.group:
        print("Gathering group statistics ..")
        group = GroupParser()
        group_userlist = list(group.group_users(args.group))
        print(group_userlist)

    # Check if the argument type is interactive
    if args.interactive:
        interactive_input(args)

    elif args.group:
        for user in group_userlist:
            generator(args, 'group', user)
    # Check if the user argument exists
    elif args.user is None :
        if not args.group:
            print(colored("[!] ", 'red') + "Username is required. Use -h for help")
            return 1
    else:
        generator(args, 'user', args.user.lower())




if __name__ == '__main__':
    main()
