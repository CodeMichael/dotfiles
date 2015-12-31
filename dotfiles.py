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
    parser.add_argument('-b',
                        '--backup',
                        dest='backup',
                        help='perform backup actions',
                        action='store_true')
    parser.add_argument('-r',
                        '--restore',
                        dest='restore',
                        help='perform restore actions',
                        action='store_true')
    parser.add_argument('-v',
                        '--verbose',
                        dest='verbose',
                        help='extra output',
                        action='store_true')
    parser.add_argument('-c',
                        '--config',
                        dest='config',
                        help='include config files',
                        action='store_true')
    parser.add_argument('-a',
                        '--atomio',
                        dest='atomio',
                        help='include atom packages',
                        action='store_true')
    parser.add_argument('-d',
                        '--dryrun',
                        dest='dryrun',
                        help='run, but don\'t actually copy anything',
                        action='store_true')
    parser.add_argument('-s',
                        '--screenshot',
                        dest='screenshot',
                        help='update the screenshot',
                        action='store_true')

    #parse the command line arguments
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.WARNING)

    #load the config file
    config_file = os.path.dirname(os.path.abspath(__file__))+'/dotfiles.json'
    try:
        with open(config_file) as configfile:
            conf = json.load(configfile)
    except IOError:
        logging.critical("I couldn't open the config file")
        exit(2)

    # set up some vars
    conf['home'] = os.environ['HOME']+'/'
    conf['configfolder'] = conf['home']+'.config/'
    conf['dotfolder'] = os.path.dirname(os.path.abspath(__file__))+'/'
    conf['atom'] = {}
    conf['atom']['listfile'] = 'atom/atom_list.json'
    conf['atom']['package_dir'] = conf['home']+'.atom/packages'

    # verbosity!
    logging.info("args: "+str(args))
    logging.info("conf: "+str(json.dumps(conf, indent=2)))

    # end
    return args, conf

def sshot(loc, args):
    """take a screenshot"""
    print('Grabbing a screenshot')
    if not args.dryrun:
        # I'm too lazy to figure out a pure python solution
        os.system('scrot '+loc+'screen.png')

def atom_mod_list(conf, args):
    """get a list of installed atom packages"""
    path = conf['atom']['package_dir']
    pkg_list = os.listdir(path)
    pkg_list.remove('README.md')
    # make it a json object
    jlist = {'packages': pkg_list}
    logging.info(json.dumps(jlist, indent=2))
    if not args.dryrun:
        with open(conf['atom']['listfile'], 'w') as jfile:
            json.dump(jlist, jfile, indent=2)

def install_atom_packages(conf, args):
    """install all atom packages"""
    with open(conf['atom']['listfile'], 'r') as pkgfile:
        pkg_list = json.load(pkgfile)
    for pkg in pkg_list['packages']:
        cmd = 'apm install '+pkg
        logging.info('Installing '+pkg)
        if not args.dryrun:
            try:
                os.system(cmd)
            except OSError as err:
                logging.warning('Faild to install '+pkg+': '+err)

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
    logging.info("filelist: "+str(json.dumps(filelist, indent=2)))
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
        print('Performing backup')
        if args.config:
            print('Backing up configs')
            copy_files('backup', file_list, conf, args)
        if args.atomio:
            print('Backing up atom package list')
            atom_mod_list(conf, args)
    elif args.restore:
        print('Performing restore')
        if args.config:
            print('Restoring config files')
            copy_files('restore', file_list, conf, args)
        if args.atomio:
            print('Installing atom.io packages')
            install_atom_packages(conf, args)
    else:
        logging.error('Your failed to specify backup or restore')
    if args.screenshot:
        sshot(conf['dotfolder'], args)
    print('Run successful, exiting...')
    exit(0)

if __name__ == '__main__':
    main()
