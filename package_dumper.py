'''
MIT License

Control-F - Android Package Dumper

Copyright (c) 2022 Control-F Ltd

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

'''

__version__ = 0.02
__author__ = 'mike.bangham@controlf.co.uk'
__description__ = 'Control-F - Android Package Dumper'

import socket
import os
from subprocess import Popen, STDOUT, PIPE
import sys
from os.path import join as pj
from os.path import abspath
import time
from datetime import timedelta


class NetCat:
    def __init__(self, ip, port, out):
        self.output = out
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, int(port)))
        self.socket.settimeout(4)

    def read(self, length=4096):
        # read 4096 bytes at a time to our tar file
        total_dumped = 0
        with open(self.output, 'wb') as f:
            while True:
                try:
                    part = self.socket.recv(length)
                    if not part:
                        break
                    f.write(part)
                    total_dumped += len(part)
                except:
                    break
        self.close()
        return total_dumped

    def close(self):
        self.socket.close()


def execute_adb(package):
    if package:
        pkg = ''
        for p in package:
            pkg += 'data/data/{} '.format(p)
    else:  # must be 'all' packages
        pkg = 'data/data/'

    p = Popen('adb forward tcp:5555 tcp:5555', shell=True, stdout=PIPE, stderr=STDOUT)
    p.wait()
    # create our pipe on the device. It is listening for a connection on the host side
    Popen('adb shell "su -c toybox tar -czh {} | toybox nc -l -p 5555"'.format(pkg))
    # delay to ensure the subprocess has executed initially
    time.sleep(2)
    # use localhost and port 5555 for transfer

    if not package:
        fn = 'data.tar.gz'
    elif len(package) > 1:
        fn = 'multi.tar.gz'
    else:
        fn = '{}.tar.gz'.format(package[0])

    nc = NetCat('127.0.0.1', '5555', abspath(pj(os.getcwd(), fn)))
    total_dumped = nc.read()
    return total_dumped


def get_file_count(pkg, serial):
    try:
        p = Popen('adb -s {} shell "su -c ls -R data/data/{} | toybox wc -l"'.format(serial, pkg),
                  shell=True, stdout=PIPE, stderr=STDOUT)
        count = p.stdout.read().decode()
        count = int(count.split('/')[0].strip())
        return count
    except:
        return False


def get_dir_size(_dir, serial):
    try:
        p = Popen('adb -s {} shell "su -c du -ks /data/data/{}"'.format(serial, _dir), shell=True, stdout=PIPE, stderr=STDOUT)
        size = p.stdout.read().decode('utf8')
        size = int(size.split('/')[0].strip()) / 1024
        return size
    except Exception as e:
        print(e)
        return False


def get_adb_device():
    info = dict(serial='', oem='', model='', installed_packages='')
    p = Popen('adb get-serialno', shell=True, stdout=PIPE, stderr=STDOUT)
    serialno = p.communicate()[0].decode().splitlines()[0]

    if serialno:
        info['serial'] = serialno
        p = Popen('adb -s {} shell getprop "| grep product.manufacturer"'.format(serialno),
                  shell=True, stdout=PIPE, stderr=STDOUT)
        oem = p.communicate()[0].decode().splitlines()[0].split(']: [')[1].replace(']', '')
        info['oem'] = oem

        p = Popen('adb -s {} shell getprop "| grep product.model"'.format(serialno),
                  shell=True, stdout=PIPE, stderr=STDOUT)
        model = p.communicate()[0].decode().splitlines()[0].split(']: [')[1].replace(']', '')
        info['model'] = model

        p = Popen('adb -s {} shell cmd package list packages -3'.format(serialno),
                  shell=True, stdout=PIPE, stderr=STDOUT)
        pkgs = p.communicate()[0].decode().replace('package:', '').splitlines()
        info['installed_packages'] = pkgs

        return info
    return False

''

if __name__ == '__main__':
    print("\n\n"
          "                                                        ,%&&,\n"
          "                                                    *&&&&&&&&,\n"
          "                                                  /&&&&&&&&&&&&&\n"
          "                                               #&&&&&&&&&&&&&&&&&&\n"
          "                                           ,%&&&&&&&&&&&&&&&&&&&&&&&\n"
          "                                        ,%&&&&&&&&&&&&&&#  %&&&&&&&&&&,\n"
          "                                     *%&&&&&&&&&&&&&&%       %&&&&&&&&&%,\n"
          "                                   (%&&&&&&&&&&&&&&&&&&&#       %&%&&&&&&&%\n"
          "                               (&&&&&&&&&&&&&&&%&&&&&&&&&(       &&&&&&&&&&%\n"
          "              ,/#%&&&&&&&#(*#&&&&&&&&&&&&&&%,    #&&&&&&&&&(       &&&&&&&\n"
          "          (&&&&&&&&&&&&&&&&&&&&&&&&&&&&&#          %&&&&&&&&&(       %/\n"
          "       (&&&&&&&&&&&&&&&&&&&&&&&&&&&&&(               %&&&&&&&&&/\n"
          "     /&&&&&&&&&&&&&&&&&&%&&&&&&&%&/                    %&&&&&,\n"
          "    #&&&&&&&&&&#          (&&&%*                         #,\n"
          "   #&&&&&&&&&%\n"
          "   &&&&&&&&&&\n"
          "  ,&&&&&&&&&&\n"
          "   %&&&&&&&&&                              {}\n"
          "   (&&&&&&&&&&,             /*             Version: {}\n"             
          "    (&&&&&&&&&&&/        *%&&&&&#\n"
          "      &&&&&&&&&&&&&&&&&&&&&&&&&&&&&%\n"
          "        &&&&&&&&&&&&&&&&&&&&&&&&&%\n"
          "          *%&&&&&&&&&&&&&&&&&&#,\n"
          "                *(######/,".format(__description__, __version__))

    print('\n\nInstructions: Requires a rooted and connected Android device\n')

    try:
        info = get_adb_device()
        print('Connected Device: {} {} ({})'.format(info['oem'], info['model'], info['serial']))
    except IndexError:
        print('No ADB devices detected\nAborting...\n\n')
        sys.exit()

    data_dir_size = get_dir_size('', info['serial'])
    if data_dir_size:
        print('\n/data/data:  [{} MB]'.format(round(data_dir_size, 2)))

    print('\nInstalled Packages:\n')
    for count, pkg in enumerate(info['installed_packages'], start=1):
        file_count = get_file_count(pkg, info['serial'])
        if file_count:
            file_count = '  [{} files]'.format(file_count)
        else:
            file_count = ''
        dir_size = get_dir_size(pkg, info['serial'])
        if dir_size:
            dir_size = '  [{} MB]'.format(round(dir_size, 2))
        else:
            dir_size = ''

        print('\t{}. {}{}{}'.format(count, pkg, file_count, dir_size))
    print('\n')

    while True:
        print("[*] Enter a package name or it's index (e.g. 2) from the list above.\n"
              "[*] To extract multiple packages, enter the package indexes separated by a comma e.g. 1,2,4\n"
              "[*] To dump all packages, type 'all'\n")
        package = input("Extract: ")
        multiple_chars = set('0123456789,')

        if package in info['installed_packages'] or package.strip().isdigit():
            start = time.time()
            if package.strip().isdigit():
                package = info['installed_packages'][int(package.strip())-1]
            print('Extracting data/data/{}...'.format(package))
            total_dumped = execute_adb([package])
            end = time.time()
            print('\nFinished! | Dumped {} MB (compressed) | Elapsed: {}\n'.format(round(total_dumped/(1024*1024),
                                                                                         2),
                                                                                   str(timedelta(seconds=end - start))))
            break

        elif package == 'all':
            start = time.time()
            print('Extracting all packages from /data/data...'.format(package))
            total_dumped = execute_adb('')
            end = time.time()
            print('\nFinished! Dumped {} MB (compressed) | Elapsed: {}\n'.format(round(total_dumped/(1024*1024),
                                                                                       2),
                                                                                 str(timedelta(seconds=end - start))))
            break

        elif any((c in multiple_chars) for c in package):
            start = time.time()
            package_list = package.strip().split(',')
            multi_packages = list()
            for p in package_list:
                multi_packages.append(info['installed_packages'][int(p.strip())-1])
            print('Extracting multiple packages from /data/data:\n\t\t{}'.format('\n\t\t'.join(multi_packages)))
            total_dumped = execute_adb(multi_packages)
            end = time.time()
            print('\nFinished! Dumped {} MB (compressed) | Elapsed: {}\n'.format(round(total_dumped / (1024 * 1024),
                                                                                       2),
                                                                                 str(timedelta(seconds=end - start))))
            break
        else:
            print('[!!] Error: {} was not found in the installed package list... try again!\n'.format(package))

    os.system('pause')
    sys.exit()
