import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify
import pandas as pd
import datetime as dt


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)
conn = engine.connect()

# Retrieve the last 12 months of precipitation data and plot the results
sql_query = 'SELECT date, prcp FROM measurement '             'WHERE date > ?'

# Calculate the date 1 year prior to the last data point in the database
last_date = dt.datetime.strptime(session.query(func.max(Measurement.date)).all()[0][0], '%Y-%m-%d')
previous_year = last_date - dt.timedelta(weeks=52)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"`/api/v1.0/<start><br/>"
        f"`/api/v1.0/<start>/<end>"
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    conn = engine.connect()

    # Perform a query to retrieve the data and precipitation scores
    precipitation_info = pd.read_sql_query(sql_query, conn, 
                                        params=[previous_year.strftime('%Y%m%d')]).dropna()
    precipitation_info['date'] = precipitation_info['date'].astype('datetime64[ns]')

    # Sort the dataframe by date
    precipitation_info.index.sort_values('date')

    return precipitation_info.to_json(orient='records')


@app.route("/api/v1.0/stations")
def stations():
    engine = create_engine("sqlite:///Resources/hawaii.sqlite")
    session = Session(engine)
    station_count = session.query(Measurement.station, func.count(Measurement.id)).group_by(Measurement.station) \
                             .order_by(func.count(Measurement.id).desc()).all()

    return jsonify(station_count)

@app.route("/api/v1.0/tobs")
def tobs():
    conn = engine.connect()
    precipitation_info = pd.read_sql_query(sql_query, conn, 
                                       params=[previous_year.strftime('%Y%m%d')]).dropna()
    precipitation_info['date'] = precipitation_info['date'].astype('datetime64[ns]')
    return precipitation_info.to_json(orient='records')

@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temps_by_date(start, end = (dt.datetime.today() + dt.timedelta(days=1))):
    engine = create_engine("sqlite:///Resources/hawaii.sqlite")
    session = Session(engine)    
    results = session.query(func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)) \
        .filter(Measurement.date >= start).filter(Measurement.date <= end).all()
    summary = list(np.ravel(results))
    return jsonify(summary)

if __name__ == '__main__':
    app.run(debug=True)
