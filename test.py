# from datetime import datetime,timezone;
# import pytz;
#
# datum=datetime.strptime("2021-11-12T12:55:46+0100", "%Y-%m-%dT%H:%M:%S%z");
# votingTimeStamp = datum.astimezone(pytz.timezone('Europe/Belgrade'));
# print(votingTimeStamp)

# list = [
#         {
#             "pollNumber": 1,
#             "name": "IndividualA",
#             "result": 0
#         },
#         {
#             "pollNumber": 2,
#             "name": "IndividualB",
#             "result": 1
#         },
#         {
#             "pollNumber": 3,
#             "name": "IndividualC",
#             "result": 1
#         }
# ]
#
# list2 = [];
#
# for item in list:
#     if item["result"] > 0:
#         list2.append(item);
#
#
# for item in list2:
#     item["result"] = "a";
#
#
# print(str(list))
# print(str(list2))
# print(5/2)

# import re
# regex = "[^@]+@.*\.[a-z]{2,}$";
# result = re.match(regex, "john@etf.bg.ac.");
# print(str(result))

from dateutil.parser import isoparse;
from datetime import datetime, timezone;

date=isoparse("2021-06-16T15:55:46");

current_time = datetime.now().replace(microsecond=0);

print(str(current_time))