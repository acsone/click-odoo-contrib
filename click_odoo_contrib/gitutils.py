# Copyright 2018 ACSONE SA/NV (<http://acsone.eu>)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import subprocess


def commit_if_needed(paths, message):
    cmd = ['git', 'add'] + paths
    subprocess.check_call(cmd)
    cmd = ['git', 'diff', '--quiet', '--exit-code', '--cached', '--'] + paths
    r = subprocess.call(cmd)
    if r != 0:
        cmd = ['git', 'commit', '-m', message, '--'] + paths
        subprocess.check_call(cmd)
        return True
    else:
        return False
