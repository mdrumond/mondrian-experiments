import re
import os
import subprocess
import sys

class Stats:
    def __init__(self):
        self.parsed = False
        self.dic = {}
    
def list_dirs(folder):
    dirs = [l for l in os.listdir(folder) if os.path.isdir(os.path.join(folder,l))]
    dirs.sort()
    return dirs

def format_num(number):
    return "%03d" % number


def get_flexpoint_folders(base_folder, phase):
    """
    run/nmp_base_64core_128MB_join_pp/flexpoint/phase_001/subphase_000/flexpoint_000/
    """

    # Get subphases
    phase_folder = os.path.join(base_folder, "phase_%s" % format_num(phase))
    subphase_folders = list_dirs(phase_folder)
    flexpoint_folders = []

    for subphase_folder in subphase_folders:
        folder = os.path.join(phase_folder,subphase_folder)
        flexpoint_folders.extend([ os.path.join(folder, l) for l in list_dirs(folder)])

    return flexpoint_folders

def gen_stats_raw(folder):
    """
    /parsacom/tools/flexus/stat-manager print all > stats.raw
    """
    filename = os.path.join(folder, 'stats.raw')
    if os.path.isfile(filename):
        return

    try:
        stats_raw = subprocess.check_output(['/home/parsacom/tools/flexus/stat-manager', 'print', 'all'],
                                            cwd=folder)
    except:
        stats_raw = "Cannot open stats database stats_db.out or stats_db.out.gz"
    
    with open(filename, 'w') as f:
        f.write(stats_raw)
    
def parse_stats_raw(folder, regexps):
    gen_stats_raw(folder)
    
    stat = Stats()
    try:
        with open(os.path.join(folder,'stats.raw'), 'r') as f:
            text = f.read()
    except:
        text = None

    if (text and
        "Cannot open stats database stats_db.out or stats_db.out.gz" not in text):
        for label, (regexp, use_findall) in regexps.iteritems():
            if use_findall:
                g = re.findall(regexp, text)
                assert len(g) != 0, "Cant parse stats.raw, file: %s, regex: %s" % (folder, regexp)
                stat.dic[label] = sum([int(d) for _,d in g])
            else:
                g = re.search(regexp, text)
                assert g is not None, "Cant parse stats.raw"
                stat.dic[label] = int(g.group(1))
        stat.parsed = True
        
    return stat

def get_flexpoint_inst_count(folder):
    """
    run for each flexpoint (run folder):

    grep from stats.raw
    Nodes-feeder-OS:Fetches                  581067657
    Nodes-feeder-User:Fetches                58881029
    """
    print("Reading instcount from %s" % folder)
    regexps = {
        "os_fetches"   : ("Nodes-feeder-OS:Fetches\s+(\d+)", False),
        "user_fetches" : ("Nodes-feeder-User:Fetches\s+(\d+)", False)}

    return parse_stats_raw(folder, regexps)

def get_flexpoint_stats_timing(folder):
    """
    Calculates
    commits per core / cycle
    total memory traffic / cycle
    row activations / cycle
    on chip messages / cycle
    off chip messages / cycle
    """
    print("Reading stats from %s" % folder)
    regexps = {
        "cycles" : ("sys-cycles\s+(\d+)", False),
        "commits" : ("Nodes-uarch-Commits\s+(\d+)", False),
        "mem_batch_msgs" : ("Nodes-batch-unroller(\d+)-batch-messages\s+(\d+)", True),
        "mem_dest_addr_access" : ("Nodes-batch-unroller(\d+)-dest-addressed-access\s+(\d+)", True),
        "mem_normal_mgs" : ("Nodes-batch-unroller(\d+)-normal messages\s+(\d+)", True),
        "net_onchip_msgs_all" : ("sys-network-Network Messages Received\s+(\d+)", False),
        "net_onchip_msgs_data" : ("sys-network-Network Messages Received:Data\s+(\d+)", False),
        "net_onchip_nodata" : ("sys-network-Network Messages Received:NoData\s+(\d+)", False),
        "net_offchip_data" : ("sys-network-Off-Chip Network Messages Received:Data\s+(\d+)", False),
        "net_offchip_nodata" : ("sys-network-Off-Chip Network Messages Received:NoData\s+(\d+)", False)
    }

    flexpoint_run = False
    stat = parse_stats_raw(folder, regexps)

    if stat.parsed:
        for k, v in stat.dic.iteritems():
            if k != 'cycles':
                stat.dic[k] = float(stat.dic[k]) / stat.dic['cycles']

    return stat


def user_pct(dic):
    return float(dic['user_fetches']) / (dic['user_fetches'] + dic['os_fetches'])

def average_everything(stats, icounts):
    stat_list = [(s.dic,i.dic) for (s, i) in zip(stats, icounts) if s.parsed]
    stat_names = [ "commits", "mem_batch_msgs", "mem_dest_addr_access", "mem_normal_mgs",
                   "net_onchip_msgs_all", "net_onchip_msgs_data", "net_onchip_nodata",
                   "net_offchip_data", "net_offchip_nodata" ]


    avg_stat = {}
    avg_stat['user_pct'] = (sum([user_pct(i) for s, i in stat_list]) / 
                            float(len(stat_list)))
    
    for name in stat_names:
        avg_stat[name] = (sum([s[name] for s,i in stat_list ]) /
                          float(len(stat_list)))

    return avg_stat;

def print_stat(avg_stat):
    for k,v in avg_stat.iteritems():
        print("%s, %0.5f" % (k ,v))

def results_nmp_npp_phase1():
    n_cores = 64
    folder_t = 'run/nmp_base_64core_128MB_join/timing'
    folder_f = 'run/nmp_base_64core_128MB_join/flexpoint'
    stats = [ get_flexpoint_stats_timing(f) for f in get_flexpoint_folders(folder_t, 1) ]
    stats = stats[:-3]
    inst_counts = [get_flexpoint_inst_count(f) for f in get_flexpoint_folders(folder_f, 1) ]
    inst_counts = [f for f in inst_counts if f.parsed]
    inst_counts = inst_counts[:-3]
    ipcs = [s.dic['commits'] / 64.0 for s in stats if s.parsed]
    icounts = [user_pct(i.dic) for i in inst_counts if i.parsed]
    print(ipcs)
    print(len(ipcs))
    print(icounts)
    print(len(icounts))

    avg_stat = average_everything(stats, inst_counts)


    print_stat(avg_stat)

def results_nmp_npp_phase0():
    n_cores = 64
    folder_t = 'run/nmp_base_64core_128MB_join/timing'
    folder_f = 'run/nmp_base_64core_128MB_join/flexpoint'
    stats = [ get_flexpoint_stats_timing(f) for f in get_flexpoint_folders(folder_t, 0) ]
    inst_counts = [get_flexpoint_inst_count(f) for f in get_flexpoint_folders(folder_f, 0) ]
    ipcs = [s.dic['commits'] / 64.0 for s in stats if s.parsed]
    icounts = [user_pct(i.dic) for i in inst_counts if i.parsed]
    print(ipcs)
    print(len(ipcs))
    print(icounts)
    print(len(icounts))

    avg_stat = average_everything(stats, inst_counts)


    print_stat(avg_stat)
    
if __name__ == "__main__":
    results_nmp_npp_phase0()
