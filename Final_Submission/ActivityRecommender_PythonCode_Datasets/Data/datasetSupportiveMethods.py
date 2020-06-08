import random
import pandas as pd

# author: Deniz Yürekdeler
# May 2020
# this program is prepared for creating random ratings,
# composing dataset from seperately collected real data
# giving ids and extracting titles and more...

#the method used to create random ratings of desired features
def randomize_ratings(file_name='Processed Data/activity-ratings-random.csv'):
    strFile = ["userId,activityId,rating\n"]

    #there will be 18 users to be equal to real data's user num.
    for userid in range(1,19):
        # each user will rate 45 random activity out of total 57 activities
        # 18 * 45 = 810 ratings (the closest number to the real ratings data which is 820 )
        activities = random.sample(range(1, 58), 45)

        for activity in activities:
            line = [str(userid)]
            line.append(str(activity))
            # rating points will be in between 1 to 5
            rate = round(random.uniform(1, 5), 1)
            line.append(str(rate))

            joined_string = ",".join(line)
            strFile.append(joined_string+"\n")

    # writing to file
    file1 = open(file_name, 'w')
    file1.writelines(strFile)
    file1.close()

#method to put ids infront of a row, inc by 1
def put_auto_inc_ids(file_name):
    L = []

    file = open(file_name, 'r')
    Lines = file.readlines()

    count = 0
    for line in Lines:
        L.append(str(count) +","+ line)
        count+=1

#method to seperate activity titles from the whole activities dataset
#this method is required to create an entity in Dialogflow
def extract_activities(file_name='activity-names.csv'):
    activity_names = pd.read_csv("activities.csv")
    names = activity_names['title']

    strList = list()
    for row in names:
        activity = '"' + row + '"'
        activity = activity + ',' + activity + "\n"
        strList.append(activity)

    file1 = open(file_name, 'w')
    file1.writelines(strList)


def create_ratings_file():
    contributed_people = ['Tesla','Mehmet','Sylvia','Rasit','Mustafa','Civan','Ulku','Dogukan','Abdullah','KaanSaglam','Dilara','Can','Deniz','KaanGircek','Omer','Taner','Bergin','Vuslat']
    empty_df = pd.DataFrame(columns=['userId', 'activityId', 'rating'])
    empty_df.to_csv(r'activity-ratings-real.csv', index = False, mode='a')

    for i in range(0, len(contributed_people)):
        person_name = contributed_people[i]
        data = pd.read_csv("Activity-Rating-Real-Data.csv", usecols=['activityId', person_name])

        data = data[data[person_name] != 0.0]
        data['userId'] = i+1

        data = data[['userId', 'activityId', person_name]]
        data.to_csv(r'activity-ratings-real.csv', index = False, mode='a', header=False)


randomize_ratings()