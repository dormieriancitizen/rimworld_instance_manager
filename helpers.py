import os, shutil, subprocess

def empty_folder(folder):
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def duplicate_check(tocheck):
    nodupes = []
    dupes = []
    for check in tocheck:
        if check not in nodupes:
            nodupes.append(check)
        else:
            dupes.append(check)
    check = nodupes
    return nodupes, dupes

def du(path):
    # Du in bytes
    return subprocess.check_output(['du','-sb', path]).split()[0].decode('utf-8')