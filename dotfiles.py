#!/usr/bin/python
"""backup or restore dotfiles"""

import json
import argparse
import os
import shutil
import logging

def config():
    """do configuration stuff"""
    parser = argparse.ArgumentParser(description='backup or restore dotfiles')
    parser.add_argument('-c',
                        '--config',
                        default='dotfiles.json',
                        dest='config',
                        help='path to config file',
                        metavar='/path/to/file')
    parser.add_argument('-b',
                        '--backup',
                        dest='backup',
                        action='store_true')
    parser.add_argument('-r',
                        '--restore',
                        dest='restore',
                        action='store_true')
    parser.add_argument('-v',
                        dest='verbose',
                        help='extra output',
                        action='store_true')
    parser.add_argument('-d',
                        dest='dryrun',
                        help='run, but don\'t actually copy anything',
                        action='store_true')
    #parse the command line arguments
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)
    #load the config file
    if args.config == 'dotfiles.json':
        config_file = os.path.dirname(os.path.abspath(__file__))+'/dotfiles.json'
    else:
        config_file = args.config
    try:
        with open(config_file) as file:
            jconf = json.load(file)
    except IOError:
        logging.critical("I couldn't open the config file")
        exit(2)
    jconf['home'] = os.environ['HOME']+'/'
    jconf['configfolder'] = jconf['home']+'.config/'
    jconf['dotfolder'] = os.path.dirname(os.path.abspath(__file__))+'/'
    logging.info("args: "+str(args))
    logging.info("jconf: "+str(jconf))
    return args, jconf

def sshot(loc, args):
    """take a screenshot"""
    print('Grabbing a screenshot')
    if not args.dryrun:
        os.system('scrot '+loc+'screen.png')

def build_file_list(conf):
    """build a list of dotfiles"""
    folders = conf['filelist']['folders']
    filelist = {}
    for folder in folders.keys():
        filelist[folder] = []
        for data in os.walk(conf['dotfolder']+folder):
            for filename in data[2]:
                strip = conf['dotfolder']+folder
                fstub = data[0][len(strip):]+'/'+filename
                filelist[folder].append(fstub)
    logging.info("filelist: "+str(filelist))
    return filelist

def copy(src, dest, args):
    """do the file copy"""
    if not args.dryrun:
        try:
            shutil.copy2(src, dest)
        except FileNotFoundError:
            logging.error(src+' could not be found, skipping...')

def copy_files(act, file_list, conf, args):
    """backup or restore dotfiles"""
    folders = conf['filelist']['folders']
    for folder in file_list.keys():
        if act == 'backup':
            source_folder = conf['home']+folders[folder]
            destination_folder = conf['dotfolder']+folder
        elif act == 'restore':
            source_folder = conf['dotfolder']+folder
            destination_folder = conf['home']+folders[folder]
        if act == 'restore':
            if not os.path.isdir(destination_folder):
                logging.info('Creating '+destination_folder)
                if not args.dryrun:
                    os.mkdir(destination_folder)
        for filename in file_list[folder]:
            src = source_folder+filename
            dest = destination_folder+filename
            logging.info("copy: "+src+" "+dest)
            copy(src, dest, args)
    files = conf['filelist']['files']
    for filename in files.keys():
        if act == 'backup':
            source_file = conf['home']+files[filename]
            destination_file = conf['dotfolder']+filename
        elif act == 'restore':
            source_file = conf['dotfolder']+filename
            destination_file = conf['home']+files[filename]
        logging.info("copy: "+source_file+" "+destination_file)
        copy(source_file, destination_file, args)

def main():
    """main function"""
    args, conf = config()
    file_list = build_file_list(conf)
    if args.backup:
        print("Performing backup")
        copy_files('backup', file_list, conf, args)
    elif args.restore:
        print("Performing restore")
        copy_files('restore', file_list, conf, args)
    else:
        logging.error('Your forgot to specify backup or restore')
    sshot(conf['dotfolder'], args)
    print('Run successful, exiting...')
    exit(0)

if __name__ == '__main__':
    main()
