from datetime import datetime
from flask import Flask, request
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
#filter deprecation warnings
import warnings
warnings.filterwarnings("ignore")

# author : Deniz Yürekdeler 2020 May
# this project implemented with using Python 3.7.x

#create the Flask app
app = Flask(__name__)


def collaborative_filtering(recommended_activities, recommended_activities_id, activity):


    #read csv files and load them to dataframes
    ratings_data = pd.read_csv("activity-ratings.csv")

    activity_names =  pd.DataFrame({'activityId':recommended_activities_id, 'title':recommended_activities})
    print(activity_names)
    #merge two dataframes, order then descending
    activity_data = pd.merge(ratings_data, activity_names, on='activityId')
    print("hello" , activity_data[activity])
    activity_data.groupby('title')['rating'].mean().head()
    activity_data.groupby('title')['rating'].mean().sort_values(ascending=False).head()
    activity_data.groupby('title')['rating'].count().sort_values(ascending=False).head()

    #groupby on column title to calculate rating mean and count for each activity
    ratings_mean_count = pd.DataFrame(activity_data.groupby('title')['rating'].mean())
    ratings_mean_count['rating_counts'] = pd.DataFrame(activity_data.groupby('title')['rating'].count())

    #visualize the rating mean and rating counts, this step is optinal
    plt.figure(figsize=(8, 6))
    plt.title("rating counts")
    plt.rcParams['patch.force_edgecolor'] = True
    ratings_mean_count['rating_counts'].hist(bins=50)

    plt.figure(figsize=(8, 6))
    plt.title("ratings")
    plt.rcParams['patch.force_edgecolor'] = True
    ratings_mean_count['rating'].hist(bins=50)
    #figures are disables for this example, uncomment code below to see figures
    #plt.show()

    #create rating matrix row column are user-activity , cells are rating
    user_activity_rating = activity_data.pivot_table(index='title', columns='userId', values='rating')
    #select the activity given by user
    print(user_activity_rating)
    similar_activity_ratings = user_activity_rating[activity]
    #find correlations of others for given activity
    activities_like_given = user_activity_rating.corrwith(similar_activity_ratings)
    #correlation dataframe
    corr_similar_activity = pd.DataFrame(activities_like_given, columns=['Correlation'])

    #drop empty cells to make dense matrix
    corr_similar_activity.dropna(inplace=True)

    #merge correlation and rating counts columns
    corr_similar_activity.sort_values('Correlation', ascending=False).head(10)
    corr_similar_activity = corr_similar_activity.join(ratings_mean_count['rating_counts'])

    #filter correlations to have minimum of 2 rating counts
    result_df = corr_similar_activity[corr_similar_activity['rating_counts'] > 5].sort_values('Correlation',
                                                                                   ascending=False).head()
    print(result_df)
    #find the given activity's title and genres
    given_activity_title = activity_names.loc[activity_names['title'] == activity, 'title'].item()
    given_activity_genres = activity_names.loc[activity_names['title'] == activity, 'genres'].item()

    #initialize title list and genres list to send them to content based filtering
    recommended_titles = list()
    recommended_genres = list()

    #add the original activity to these lists
    recommended_titles.append(given_activity_title)
    recommended_genres.append(given_activity_genres)

    #loop result dataframe of collaborative filtering
    for index, row in result_df.iterrows():
        #find the time, season and genres of the current activity
        activity_title = row.name
        time = activity_names.loc[activity_names['title'] == activity_title, 'time'].item()
        season = activity_names.loc[activity_names['title'] == activity_title, 'season'].item()
        genres = activity_names.loc[activity_names['title'] == activity_title, 'genres'].item()
        #control if the activity is logical for current season & time, if so add it to lists
        time_check, season_check = check_approporiate(time, season)
        if time_check and season_check:
            activity_name = str(activity_title)
            recommended_titles.append(activity_name)
            recommended_genres.append(genres)

    #call content based filtering with the filtered results
    # recommendations = content_based(recommended_titles, recommended_genres, activity)

    response_str = "<h1>The activity(s) I recommend for you : " + recommended_titles + "</h1>"
    #result is printed in console incase user cannot use a web browser
    print(response_str)
    #for viewing the reulst in a web browser we send the result str in json form
    #for using this API from other apps. send the recommendations list instead of response_str
    return ''' {} '''.format(response_str)

#find current hour and season
def time_and_season():
    now = datetime.now()
    month = now.month
    hour = now.hour

    if 3 <= month <= 5:
        season = "spring"
    elif 6 <= month <= 8:
        season = "summer"
    elif 9 <= month <= 11:
        season = "fall"
    else:
        season = "winter"
    if hour < 18:
        time = "day"
    else:
        time = "evening"

    return time, season

def check_approporiate( time, season):
    #find current time and season from other supportive method
    time_now, season_now = time_and_season()
    time_check = False
    season_check = False

    if time == "all" or time == time_now:
        time_check = True
    if season == "all" or str(season).__contains__(str(season_now)):
        season_check = True

    return time_check, season_check

# this route : http:// example url /
@app.route('/',methods=['GET', 'POST'])
def content_based():
    activity = 'going-concert'
    activity_id = '20'
    #create a new dataframe with title and genres lists
    #df = pd.DataFrame({'title':activity_names, 'genres':genres})

    activity_names = pd.read_csv("activities.csv")

    df = activity_names[['title', 'genres']]
    df.head()

    # initialize the new column to hold found keywords
    df['Key_words'] = ""

    #loop the dataframe created
    for index, row in df.iterrows():

        #initialize vectorizer for NLP
        vectorizer = TfidfVectorizer()

        # extracting the words by passing the text
        vectorizer.fit_transform(row)

        # getting the dictionary with key words as keys and their scores as values
        key_words_dict_scores = vectorizer.get_feature_names()

        # assigning the key words to the new column for the corresponding movie
        row['Key_words'] = list(key_words_dict_scores)

    # instantiating and generating the count matrix
    count = CountVectorizer()
    count_matrix = count.fit_transform(df['Key_words'].astype('str'))

    # generating the cosine similarity matrix
    cosine_sim = cosine_similarity(count_matrix, count_matrix)

    # gettin the index of the activity that matches the title
    idx = df.index[df['title'] == activity].tolist()[0]

    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(cosine_sim[idx]).sort_values(ascending=False)

    # getting the indexes of the 5 most similar activities
    top_10_indexes = list(score_series.iloc[1:11].index)

    # initializing the empty list to hold the recommendations
    recommended_activities = list()
    recommended_activities_id = list()
    recommended_activities.append(activity)
    recommended_activities_id.append(activity_id)
    for i in top_10_indexes:
        recommended_activities_id.append(i+1)
        recommended_activities.append((df['title'].loc[i]))


    print(recommended_activities)

    #now remove the original activity to not recommend it back to the user


    #append recommendations with comma
    #return " ,".join(recommended_activities)

    collaborative_filtering(recommended_activities, recommended_activities_id, activity)

if __name__ == "__main__":
    app.run(port=8080, debug=True)
