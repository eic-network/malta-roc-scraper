import os
import sys

import gather
import lookup


def main():
    # gather2.main()
    gather_list = len(eval(open('gather.json2').read()))
    gotten = len((os.listdir('output3')))
    while gotten < gather_list-1:
        try:
            lookup.set_list_start(gotten)
            lookup.main()
        except:
            gotten = len((os.listdir('output3')))


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
