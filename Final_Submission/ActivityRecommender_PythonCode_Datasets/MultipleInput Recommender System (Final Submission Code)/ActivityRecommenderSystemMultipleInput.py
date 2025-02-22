from datetime import datetime
from flask import Flask, request
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
# filter deprecation warnings
import warnings

warnings.filterwarnings("ignore")

# author : Deniz Yürekdeler 2020 May
# this project is implemented with using Python 3.7.x

# create the Flask app
app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def collaborative_filtering():
    req = request.get_json(force=True)
    activity_list = req['activity_list']

    # read csv files and load them to dataframes
    ratings_data = pd.read_csv("../Data/Processed Data/activity-ratings-real.csv")
    activity_names = pd.read_csv("../Data/Processed Data/activities.csv")

    # merge two dataframes, order then descending
    activity_data = pd.merge(ratings_data, activity_names, on='activityId')
    activity_data.groupby('title')['rating'].mean().head()
    activity_data.groupby('title')['rating'].mean().sort_values(ascending=False).head()
    activity_data.groupby('title')['rating'].count().sort_values(ascending=False).head()

    # groupby on column title to calculate rating mean and count for each activity
    ratings_mean_count = pd.DataFrame(activity_data.groupby('title')['rating'].mean())
    ratings_mean_count['rating_counts'] = pd.DataFrame(activity_data.groupby('title')['rating'].count())

    # visualize the rating mean and rating counts, this step is optinal
    # plt.figure(figsize=(8, 6))
    # plt.title("rating counts")
    # plt.rcParams['patch.force_edgecolor'] = True
    ratings_mean_count['rating_counts'].hist(bins=50)

    # plt.figure(figsize=(8, 6))
    # plt.title("ratings")
    # plt.rcParams['patch.force_edgecolor'] = True
    ratings_mean_count['rating'].hist(bins=50)

    # uncomment this line to see the figures
    # plt.show()

    # create rating matrix row column are user-activity , cells are rating
    user_activity_rating = activity_data.pivot_table(index='userId', columns='title', values='rating')

    recommendation_list = list()
    for activity in activity_list:
        print(" -- Finding recommendation for the given activity : ", activity)
        curr_activity_name = activity_names.loc[activity_names['title'] == activity, 'title'].item()
        curr_activity_genres = activity_names.loc[activity_names['title'] == activity, 'genres'].item()

        recommended_titles = list()
        recommended_genres = list()

        result_df = calculate_correlation(activity, user_activity_rating, ratings_mean_count)
        print(result_df)
        for index, row in result_df.iterrows():

            activity_title = row.name
            time = activity_names.loc[activity_names['title'] == activity_title, 'time'].item()
            season = activity_names.loc[activity_names['title'] == activity_title, 'season'].item()
            genres = activity_names.loc[activity_names['title'] == activity_title, 'genres'].item()

            time_check, season_check = check_approporiate(time, season)
            if time_check and season_check:
                activity_name = str(activity_title)
                recommended_titles.append(activity_name)
                recommended_genres.append(genres)

        if curr_activity_name not in recommended_titles:
            recommended_titles.append(curr_activity_name)
            recommended_genres.append(curr_activity_genres)

        print(" ---- Collaborative Filtering Result: ", recommended_titles)
        recommendations = content_based(recommended_titles, recommended_genres, activity)
        print(' ---- Content Based Filtering Result: ', recommendations)
        for reco in recommendations:
            if reco not in recommendation_list:
                recommendation_list.append(reco)

    for act in activity_list:
        if act in recommendation_list:
            recommendation_list.remove(act)

    response_str = "<h1>The activity(s) I recommend for you : " + ", ".join(recommendation_list) + "</h1>"

    return ''' {} '''.format(response_str)


def calculate_correlation(activity, user_activity_rating, ratings_mean_count):
    # select the activity given by user
    similar_activity_ratings = user_activity_rating[activity]
    # find correlations of others for given activity
    activities_like_given = user_activity_rating.corrwith(similar_activity_ratings)
    # correlation dataframe
    corr_similar_activity = pd.DataFrame(activities_like_given, columns=['Correlation'])

    # drop empty cells to make dense matrix
    corr_similar_activity.dropna(inplace=True)

    # merge correlation and rating counts columns
    corr_similar_activity.sort_values('Correlation', ascending=False).head(10)
    corr_similar_activity = corr_similar_activity.join(ratings_mean_count['rating_counts'])

    # filter correlations to have minimum of 2 rating counts
    result_df = corr_similar_activity[corr_similar_activity['rating_counts'] > 7].sort_values('Correlation',
                                                                                              ascending=False).head()
    return result_df


# find current hour and season
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


def check_approporiate(time, season):
    # find current time and season from other supportive method
    time_now, season_now = time_and_season()
    time_check = False
    season_check = False

    if time == "all" or time == time_now:
        time_check = True
    if season == "all" or str(season).__contains__(str(season_now)):
        season_check = True

    return time_check, season_check


def content_based(activity_names, genres, activity):
    # create a new dataframe with title and genres lists
    df = pd.DataFrame({'title': activity_names, 'genres': genres})
    df = df[['title', 'genres']]

    # initialize the new column to hold found keywords
    df['Key_words'] = ""

    # loop the dataframe created
    for index, row in df.iterrows():
        # initialize vectorizer for NLP
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
    top_3_indexes = list(score_series.iloc[1:4].index)

    # initializing the empty list to hold the recommendations
    recommended_activities = list()
    for i in top_3_indexes:
        recommended_activities.append((df['title'].loc[i]))

    # now remove the original activity to not recommend it back to the user
    # fix here
    if recommended_activities.__contains__(activity):
        recommended_activities.remove(activity)

    # append recommendations with comma
    return recommended_activities


if __name__ == "__main__":
    app.run(port=8080, debug=True)
