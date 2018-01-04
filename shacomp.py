import sys
import glob, re, fnmatch, os
import collections
import shutil
import hashlib

import numpy as np
# import matplotlib.pyplot as plt

import matplotlib

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

sha_kind = 'sha512'


def plot(c):
    # labels, values = zip(*Counter(['A','B','A','C','A','A']).items())
    labels, values = zip(*c.items())

    indexes = np.arange(len(labels))
    width = 1

    plt.bar(indexes, values, width)
    plt.xticks(indexes + width * 0.5, labels)
    plt.show()


def isJunkFile(filename):
    junk = ["thumbs.db", "desktop.ini", "picasa.ini", ".picasa.ini", "picasa.ini1", ".picasa.ini1"]
    return (os.path.basename(filename).lower() in junk)


def readfile(filename, d, d_ext, uniquelog=None, siglen=0):
    # with open(filename, encoding="utf-8-sig").read().decode("utf-8-sig") as f:
    with open(filename, mode='r', encoding="utf-8-sig") as f:
        print("{} ...".format(filename))
        valid_count = 0
        total_lines = 0
        junk_count = 0
        new_unique_count = 0
        if siglen == 0:
            siglen = 128
        delim = ' *'
        invalid = []
        for line in f:
            # line=line.rstrip('\n')
            line = line.strip()
            if (line == ''):
                continue
            total_lines += 1
            kv = line.split(delim, 1)
            if (len(kv) != 2) or (len(kv[0]) != siglen) or (len(kv[1]) == 0):
                invalid.append(line)
            else:
                key = kv[0].lower()
                val = kv[1]
                if isJunkFile(val):
                    junk_count += 1
                else:
                    # d.setdefault(key,[])
                    # d.append(val)
                    ext = os.path.splitext(val)[1]
                    d_ext[ext] += 1
                    valid_count += 1
                    if not val in d[key]:
                        d[key].append(val)
                        if len(d[key]) == 1:
                            new_unique_count += 1
                            if not (uniquelog is None):
                                uniquelog.append([key, val])
    # unique_count = len(d)
    invalid_count = len(invalid)
    verify_total = valid_count + invalid_count + junk_count
    print("valid: {}(unique: {} + dups: {}) + invalid: {} + junk: {} = total: {} entries, ({})".
          format(filename, valid_count, new_unique_count, valid_count - new_unique_count,
                 invalid_count, junk_count, total_lines, verify_total == verify_total))
    printstats(d)
    print('ext list:')
    print(d_ext)


def printstats(d):
    c, hist = sumDefaultDict(d)
    total = sum(c.values())
    print("dict stats: unique entries:{}/{}".format(len(d), total))
    # plot(hist)
    return c


# returns a list of tuples [ (key val)...]
def getUniqueTupListFromDict(d):
    l = []
    for key, value in d.items():
        l.append((key, value[0]))  # append only key and first val
    l.sort(key=lambda tup: tup[1])  # sorts in place
    return l


def saveTupList(l, filename):
    text_file = open(filename, "w", -1, "utf-8-sig")
    count = len(l)
    for k, v in l:
        s = '{0} *{1}\n'.format(k, v)
        text_file.write(s)
    print("Writing: {0}: {1} lines".format(filename, count))
    text_file.close()


# def readoutfile( d, filename):
#     with open(filename) as f:
#         total_lines=0
#         for line in f:
#             line=line.strip().rstrip('\n')
#             if line=='':
#                 continue
#             total_lines+=1
#             kv=re.split(r'\t+', line)
#             key = kv[0]
#             val = kv[1]
#             d[key] = val
#     print("{0}: base lines: {1}".format(filename,total_lines))
#
# def writefile(d, filename):
#     od = collections.OrderedDict(sorted(d.items()))
#     count = len(od)
#     if count>0:
#         text_file = open(filename, "w")
#         for k, v in od.iteritems():
#             s='{0}\t{1}\n'.format(k,v)
#             text_file.write(s)
#         print("Writing: {0}: {1} lines".format(filename,count))
#         text_file.close()
#     else:
#         print("No items found!")


def sumDefaultDict(d):
    c = collections.Counter()  # for each key the value length
    hist = collections.Counter()  # count the number of keys that have the same value length
    for key, value in d.items():
        l = len(value)  # number of entries for this key
        c[key] = l
        hist[l] += 1
    return c, hist


def read_write(dir, master, ext='.' + sha_kind):
    # d = {}
    # key = hash
    # value = list of files
    d = collections.defaultdict(list)
    d_ext = collections.Counter()
    # c = collections.Counter(value for values in d.itervalues() for value in values)
    # dir=os.getcwd()
    if dir != '':
        os.chdir(dir)

    base_file = master + ext
    filename = base_file
    # if a base file is provided, read it, otherwise continue to read in alphabetical order
    if filename != '':
        s = os.path.join(dir, filename)
        if os.path.isfile(s):
            print("0:")
            readfile(s, d, d_ext)
            print()
            # s = os.path.join(dir,filename+"-uniques"+ext)
            # saveTupList(uniquelog, s)

    in_pattern = '*' + ext
    # for filename in re.compile(fnmatch.translate(in_pattern), re.IGNORECASE):

    sha_files_count = 1
    for filename in sorted(glob.glob(in_pattern)):
        if filename == base_file or ("unique" in filename) or ("ignore" in filename):
            continue
        print('{}:'.format(sha_files_count))
        s = os.path.join(dir, filename)
        uniquelog = []
        readfile(s, d, d_ext, uniquelog)
        if len(uniquelog) > 0:
            s = os.path.join(dir, os.path.splitext(filename)[0] + "-uniques" + ext)
            saveTupList(uniquelog, s)
        # writefile(d, os.path.join(dir, outfile))
        print("{} new unique files from file:{}, base file:{}".format(len(uniquelog), filename, base_file))
        print()
        sha_files_count += 1

    print("\n---- finished loading {} sha files ---- \n".format(sha_files_count))

    l = getUniqueTupListFromDict(d)
    s = os.path.join(dir, "uniques" + ext)
    saveTupList(l, s)
    return d


def sha512_file(fname):
    hash = hashlib.sha512()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()


def del_dups(dir, d, verify_sha=True, verify_sha_allcopies=True):
    print('delete dups from dir: {}'.format(dir))
    total = 0
    firsts = []
    sha_ok = []
    deleted = []
    sha_err = []
    missing = []
    for key, value in d.items():
        copyfound = False
        isFirst = True
        for f in value:
            filename = os.path.join(dir, f)
            currfound = os.path.isfile(filename)
            total += 1
            if currfound:
                shahex = sha512_file(filename)
                sha_verified = key == shahex
                if sha_verified:
                    sha_ok.append(filename)
                    if isFirst:
                        firsts.append(filename)
                    isFirst = False
                else:
                    sha_err.append(filename)
                    print('err #{:5d}: {}'.format(len(sha_err), filename))
            else:
                missing.append(filename)
                print('mis #{:5d}: {}'.format(len(missing), filename))
                sha_verified = False

            if copyfound:
                # found a concrete duplicate
                if sha_verified:
                    os.remove(filename)
                    deleted.append(filename)
                    print('del #{:5d}: {}'.format(len(deleted), filename))
            else:
                copyfound = sha_verified

    print('total: {}; [missing: {}; sha_err: {}; sha_ok: {}; firsts: {}; deleted: {}'.
          format(total, len(sha_ok), len(missing), len(sha_err), len(firsts), len(deleted)))


def restore_dups(dir, d):
    restored = 0
    restored_failed = []
    total = 0
    totalfound = 0
    firstsFound = 0
    restored_list = []
    restored_failed_list = []
    for key, value in d.items():
        isFirst = True
        thisSource = None
        for f in value:
            filename = os.path.join(dir, f)
            currfound = os.path.isfile(filename)
            total += 1
            if currfound:
                if isFirst:
                    firstsFound += 1
                totalfound += 1
                if thisSource == None:
                    thisSource = filename
            else:
                if thisSource != None:
                    shutil.copyfile(thisSource, filename)
                if os.path.isfile(filename):
                    restored += 1
                    restored_list.append(filename)
                else:
                    restored_failed += 1
                    restored_failed_list.append(filename)
            isFirst = False

    print('total: {}; found: {}; firsts: {}; restored: {}; restored_failed: {}'.
          format(total, totalfound, firstsFound, restored, restored_failed))


#
# if len(sys.argv) >= 2:
#     dir = sys.argv[1]
# else:
#     dir = r''
#
# if len(sys.argv) >= 3:
#     base_file = sys.argv[2]
# else:
#     base_file = 'base.txt'
#
# if len(sys.argv) >= 4:
#     in_pattern = sys.argv[3]
# else:
#     in_pattern = '*.NEW'
#
# if len(sys.argv) >= 5:
#     outfile = sys.argv[4]
# else:
#     outfile = 'NEW_PRICE_LIST.txt'

# read_write(dir, base_file, in_pattern, outfile)
# read_write(dir=r"d:\git\shacomp\sha2", master="Pictures-20170311")
base_dir = r"d:\git\shacomp\sample"
d = read_write(dir=base_dir, master="0")
# del_dups(dir=base_dir, d=d)
restore_dups(dir=base_dir, d=d)
# os.system("pause")
