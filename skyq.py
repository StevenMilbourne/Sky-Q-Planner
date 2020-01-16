import requests
import json
from datetime import datetime
import datetime as dt
from IPy import IP


# The goal of this script is to request a list of shows from a Sky Q Box that are due to be recorded on the current day.
# As Sky will automatically record shows you often watch,
# this serves as a basic, personalised list of shows that you are likely to watch that day.
# The script produces a JSON object that can easily be used with many platforms.
# I peronsally use this with a Hotword detector and voice command that will obtain this list,
# then read it out to me as an audio response, in addition to displaying the info on a Smart Mirror


# Known issues/areas to improve

# The list of shows(as dictionaries) will occasionally contain shows that are not in the correct place
# in terms of start time. This means that setting a greater limit value may be necessary.
# However in practice it should rarely be a problem, if ever.

# See if the error handling can be less general and include more cases

# Can all the info be obtained from the sky box with a single request?



class SkyBox(object):
    # Set the default limit to 50 as that should be more than plenty
    def __init__(self, addr, limit = 50):

        # IP module will throw an error if an invalid IP Address is used
        try:
            self.addr = IP(addr)

        except ValueError as e:
            raise ValueError("Incorrect IP Address Format")

        # The port for a Sky Q or Sky Q Mini is 9006 by default
        self.port = 9006

        # For the purposes of this script there is no need to request all items
        self.limit = limit

        # Check that the IP address points to a valid SkyQ box
        try:
            self.req = requests.get('http://{}:{}/as/pvr?limit=0&offset=0'.format(self.addr, self.port))

        except requests.exceptions.RequestException as e:
            raise requests.exceptions.RequestException('Connection Error - Could Not Create SkyBox Object')


    @property
    def getSchedule(self):
        # Jsonify the returned request data to make it subscriptable
        pvr = self.req.json()

        # Offset value is needed to make a full request to the Sky Box
        # The initial request is used to get the total number of shows in your PRV
        # This is then used to calculate the offset
        offset = pvr['totalPvrItems'] - self.limit

        # Make the full request
        newreq = requests.get("http://{}:{}/as/pvr?limit={}&offset={}".format(self.addr, self.port, self.limit, offset))
        shows = newreq.json()

        # Extract the info we need
        shows = shows["pvrItems"]

        # Get tommorow's date as a Unix Timestamp
        # Change hour value if you want to include shows scheduled after midnight (0-23)
        datetomorrow = datetime.timestamp(dt.datetime.combine(dt.date.today(), dt.time(hour=0)) + dt.timedelta(days=1))

        # Create a list of shows that are scheduled to be recorded before tommorow
        onToday = [show for show in shows if show['status'] == 'SCHEDULED' and show['st'] < datetomorrow]

        # Sort the shows by their timestamp
        onToday = sorted(onToday, key=lambda i=0: i['st'])

        # Create a new list with only the relevant information
        schedule = []
        for show in onToday:

            # It shouldn't be possible for a show to have no title
            try:
                title = show["t"]
            except KeyError:
                title = ""

            try:
                season = show["seasonnumber"]
            except KeyError:
                season = ""

            try:
                episode = show["episodenumber"]
            except KeyError:
                episode = ""

            try:
                starttime = datetime.fromtimestamp(show['st']).strftime('%H:%M')
            except KeyError:
                starttime = ""

            schedule.append({"title": title, "season": season, "episode": episode, "starttime": starttime})

        return schedule


if __name__ == '__main__':

    boxip = input("Please enter the IP  of the Sky Q Box that you wish to connect\n")

    try:
        skyBox = SkyBox(boxip, 50)
        schedule = skyBox.getSchedule
        [print(show) for show in schedule]

    except Exception as e:
        print(e)


