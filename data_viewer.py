import os 
import json
import tqdm
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as md
import numpy as np
import datetime as dt

J = os.path.join  
E = os.path.exists
F =  os.path.isfile

AUG17 = 1534464000*1000
BEGIN = 1531785600*1000

import constants

#bases = [
#	"/run/user/1000/gvfs/smb-share:server=192.168.1.15,share=renderbox_test_output/rendered_new",
#	"/run/user/1000/gvfs/smb-share:server=192.168.1.15,share=renderbox_test_output/rendered_old"]
bases = [constants.RENDER_DIR]


records = []
for base in bases:
	records  += [x[0] for x in os.walk(base)]

rwm = [
    x for x in records if E(J(x,'metaData.json'))]
# and E(J(x, 'VALID'))]


records_with_metadata = []
records_metadata = []
for x in tqdm.tqdm(rwm):
    with open(J(x,'metaData.json'), 'r') as f:
        try:
            records_metadata.append(json.load(f))
            records_with_metadata.append(x)
            if not 'date' in x or  not x['date']:
                x['date'] = BEGIN
        except Exception as e:
            pass


record_durations = [m['duration'] for m in records_metadata]
new_record_durations =  [m['duration'] for m in records_metadata] 

time_ordered_recordings = sorted(records_metadata, key=lambda x: x['date'])
cum_durations = np.cumsum(list(map(lambda x: x['duration'], time_ordered_recordings)))/1000/60/60
timestamps = list(map(lambda x: int(x['date']/1000), time_ordered_recordings))

dates=[(dt.datetime.fromtimestamp(ts) if not ts == -1 else timestamps[-1]) for ts in timestamps]
datenums=md.date2num(dates)


 
# Duration plot
plt.title("Hours recorded")
ax=plt.gca()
xfmt = md.DateFormatter('%Y-%m-%d')
ax.xaxis.set_major_formatter(xfmt)
plt.xticks( rotation=25 )
plt.plot(datenums, cum_durations)
# plt.xlim([md.date2num(dt.datetime.fromtimestamp(BEGIN//1000))  , md.date2num(dt.datetime.now())])
plt.show()

print("Progress")
print("\tTotal number of hours valid: {}".format(sum(record_durations)/1000/60/60))
print("\tTotal frames recorded: {}".format(sum(record_durations)/50))
print("\tTotal hours since August 17: {}".format(sum(new_record_durations)/1000/60/60))
print("\tLongest session: {}".format(max(record_durations)/1000/60/60))



# dbase = "/run/user/1000/gvfs/smb-share:server=192.168.1.15,share=renderbox_test_output/downloaded"


# downloads  = [J(dbase, y) for y in [x[2] for x in os.walk(dbase) if x[0] == dbase][0] ]

# streams =  list(set([x.split('-2018')[0].split(dbase + "/")[-1] for x in downloads 
#     if '2018-08-' in x ]))
# stream_sizes = [ sum([os.stat(f).st_size for f in downloads if stream in f]) for stream in streams]
# human_stream_sizes = [ x/(1024*1024) for x in stream_sizes]

# stream_info = list(zip(streams, human_stream_sizes))

# # merged
# mbase =  "/run/user/1000/gvfs/smb-share:server=192.168.1.15,share=renderbox_test_output/merged"

# merged = {
#     y.split(".")[0]:  (J(mbase, y), os.stat(J(mbase, y)).st_size)

#     for y in [x[2] for x in os.walk(mbase) if x[0] == mbase][0]
# }
# merged_info = dict(zip(merged, streams))
# #
# goodinfo = sorted(
#     [(s, i, merged[s][1]/1024/1024) for s,i in stream_info if J(base, s) in records_with_metadata],
#     key = lambda x: x[2])



# # Good boys for  streaminfo.
# good_boys =sorted([(s, i)  for s,i in  stream_info if  s in records_with_metadata], key=lambda x: x[1])
