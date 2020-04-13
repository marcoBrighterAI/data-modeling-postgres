import os
import glob
import psycopg2
import pandas as pd
from sql_queries import *


def process_song_file(cur, filepath):
    """
    Function that reads a song file and inserts its data to songs and artists tables.
    :param cur: psycopg2 cursor
    :param filepath: the path to the json file
    """
    # open song file
    df = pd.read_json(filepath, lines=True)

    # insert song record
    song_data = (df.values[0][7], df.values[0][8], df.values[0][0], df.values[0][9], df.values[0][5])
    cur.execute(song_table_insert, song_data)
    
    # insert artist record
    artist_data = (df.values[0][0], df.values[0][4], df.values[0][2], df.values[0][1], df.values[0][3])
    cur.execute(artist_table_insert, artist_data)


def process_log_file(cur, filepath):
    """
    Function that reads a log file and inserts its data to time, users and songplays tables.
    :param cur: psycopg2 cursor
    :param filepath: the path to the json file
    """
    # open log file
    df = pd.read_json(filepath, lines=True)

    # filter by NextSong action
    df = df[df['page'] == 'NextSong']

    # convert timestamp column to datetime
    t = pd.to_datetime(df['ts'], unit='ms')
    
    # insert time data records
    time_df = pd.DataFrame(columns=['time', 'hour', 'day', 'week_of_year', 'month', 'year', 'weekday'])
    time_df['time'] = df['ts']
    time_df['hour'] = t.dt.hour
    time_df['day'] = t.dt.day
    time_df['week_of_year'] = t.dt.weekofyear
    time_df['month'] = t.dt.month
    time_df['year'] = t.dt.year
    time_df['weekday'] = t.dt.weekday

    for i, row in time_df.iterrows():
        cur.execute(time_table_insert, list(row))

    # load user table
    user_df = df[['userId','firstName', 'lastName', 'gender', 'level']]

    # insert user records
    for i, row in user_df.iterrows():
        cur.execute(user_table_insert, row)

    # insert songplay records
    for index, row in df.iterrows():
        
        # get songid and artistid from song and artist tables
        cur.execute(song_select, (row.song, row.artist, row.length))
        results = cur.fetchone()
        
        if results:
            songid, artistid = results
        else:
            songid, artistid = None, None

        # insert songplay record
        songplay_data = (index, row.ts, row.userId, row.level, songid, artistid, row.sessionId, row.location, row.userAgent)
        cur.execute(songplay_table_insert, songplay_data)


def process_data(cur, conn, filepath, func):
    """
    Function that reads all files from filepath and porcesses it.
    :param cur: psycopg2 cursor
    :param conn: database connection
    :param filepath: the path to the json file
    :param filepath: location of files to be processed
    :param func: function to execute (process_song_file or process_log_file)
    """
    # get all files matching extension from directory
    all_files = []
    for root, dirs, files in os.walk(filepath):
        files = glob.glob(os.path.join(root,'*.json'))
        for f in files :
            all_files.append(os.path.abspath(f))

    # get total number of files found
    num_files = len(all_files)
    print('{} files found in {}'.format(num_files, filepath))

    # iterate over files and process
    for i, datafile in enumerate(all_files, 1):
        func(cur, datafile)
        conn.commit()
        print('{}/{} files processed.'.format(i, num_files))


def main():
    conn = psycopg2.connect("host=127.0.0.1 dbname=sparkifydb user=student password=student")
    cur = conn.cursor()

    process_data(cur, conn, filepath='data/song_data', func=process_song_file)
    process_data(cur, conn, filepath='data/log_data', func=process_log_file)

    conn.close()


if __name__ == "__main__":
    main()
