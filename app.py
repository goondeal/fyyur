import json
import dateutil.parser
import babel
from datetime import datetime
from flask import Flask, render_template, request, Response, flash, redirect, url_for, jsonify
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from config import db, app


# Models.
# Implement Show, Venue and Artist models, and complete all model relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = 'shows'
    id = db.Column('id', db.Integer, primary_key=True)
    venue_id = db.Column('venue_id', db.Integer, db.ForeignKey('venues.id'), nullable=False)
    artist_id = db.Column('artist_id', db.Integer, db.ForeignKey('artists.id'), nullable=False)
    start_time = db.Column('start_time', db.String(), nullable=False)
    artist = db.relationship('Artist', back_populates='venues')
    venue = db.relationship('Venue', back_populates='artists')


venue_seeking_description = "We are on the lookout for a local artist to play every two weeks. Please call us."


class Venue(db.Model):
    __tablename__ = 'venues'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String())
    # implement any missing fields, as a database migration using Flask-Migrate.
    genres = db.Column(db.String(), nullable=False)
    website = db.Column(db.String())
    seeking_talent = db.Column(db.Boolean, default=True)
    seeking_description = db.Column(db.String(), default=venue_seeking_description)
    artists = db.relationship('Show', back_populates='venue') 


class Artist(db.Model):
    __tablename__ = 'artists'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    # implement any missing fields, as a database migration using Flask-Migrate.
    website = db.Column(db.String())
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String())
    venues = db.relationship('Show', back_populates='artist')


# Filters.
def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# Controllers.
@app.route('/')
def index():
    return render_template('pages/home.html')

def venue_to_json(venue):
    return {
        "id": venue.id,
        "name": venue.name,
        # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
        "num_upcoming_shows": Show.query.filter(Show.venue_id == venue.id, Show.start_time > str(datetime.now())).count(),
    }


# Venues
@app.route('/venues')
def venues():
    # get all venues
    venues = Venue.query.all()
    # get cities set
    cities = set(map(lambda venue: venue.city, venues))
    data = []
    # for each city, get all venues in this city. 
    for city in cities:
        venues_in_city = list(filter(lambda venue: venue.city == city, venues))
        data.append({
            "city": city,
            "state": venues_in_city[0].state,
            "venues": list(map(lambda venue: venue_to_json(venue), venues_in_city))
        })
    # Redirect with data.
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # implement search on venues with partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(\
        # search_term is in venue.name
        Venue.name.ilike(f'%{search_term}%') | \
        # OR venue.name starts with search_term
        Venue.name.ilike(f'{search_term}%') | \
        # OR venue.name ends with search_term
        Venue.name.ilike(f'%{search_term}')).order_by('id').all()

    response = {
        "count": len(venues),
        "data": list(map(lambda venue: {'id': venue.id, 'name': venue.name, 'num_upcoming_shows': Show.query.filter(Show.venue_id == venue.id, Show.start_time > str(datetime.now())).count()}, venues))
    }
    # Redirect with data.
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


def show_to_json_lite(show):
    artist = Artist.query.get(show.artist_id)
    return {
        "artist_id": artist.id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time, 
    }


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id.
    venue = Venue.query.get(venue_id)
    # Get all shows for this venue.
    shows = Show.query.filter_by(venue_id= venue_id).all()
    print(f'shows = {shows}')
    # past shows.
    past_shows = list(filter(lambda show: show.start_time < str(datetime.now()), shows))
    past_shows_count = len(past_shows)
    # upcoming shows.
    upcoming_shows = list(filter(lambda show: show.start_time >= str(datetime.now()), shows))
    upcoming_shows_count = len(upcoming_shows)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "image_link": venue.image_link,
        "past_shows": list(map(show_to_json_lite, past_shows)),
        "upcoming_shows": list(map(show_to_json_lite, upcoming_shows)),
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count,
    }
    # Redirect with data.
    return render_template('pages/show_venue.html', venue=data)


# Create Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # insert form data as a new Venue record in the db, instead
    try:
        # Get form data.
        name = request.form['name']
        city = request.form['city']
        state = request.form['state']
        address = request.form['address']
        genres = request.form['genres']
        # Nullable values
        phone = request.form.get('phone', '')
        facebook_link = request.form.get('facebook_link', '')
        # create new venue object, then add it.
        venue = Venue(name=name, city=city, state=state, address=address, phone=phone, genres=genres, facebook_link=facebook_link)
        # print(venue.genres)
        db.session.add(venue)
        # commit changes.
        db.session.commit()
        # on successful db insert, flash success.
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()
    # TODO: modify data to be the data object returned from db insertion
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        Venue.query.get(venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return None


#  Artists
@app.route('/artists')
def artists():
    # replace with real data returned from querying the database
    artists = Artist.query.all()
    data = list(map(lambda artist: {'id': artist.id, 'name': artist.name}, artists))
    # Redirect with data.
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term=request.form.get('search_term', '')
    artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%') | Artist.name.ilike(f'{search_term}%') | Artist.name.ilike(f'%{search_term}')).order_by('id').all()
    response = {
        "count": len(artists),
        "data": list(map(lambda artist: {'id': artist.id, 'name': artist.name, 'num_upcoming_shows': db.session.query(Show).filter(Show.artist_id == artist.id, Show.start_time > str(datetime.now())).count()}, artists))
    }
    # Redirect with data.
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


def show_to_json_venue(show):
    venue = Venue.query.get(show.venue_id)
    return {
        'venue_id': venue.id,
        'venue_name': venue.name, 
        'start_time': show.start_time, 
        'venue_image_link': venue.image_link,
    }

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get(artist_id)
    # get all the shows for this artist.
    shows = Show.query.filter_by(artist_id= artist_id).all()
    # past shows.
    past_shows = list(filter(lambda show: show.start_time < str(datetime.now()), shows))
    past_shows_count = len(past_shows)
    # upcoming shows.
    upcoming_shows = list(filter(lambda show: show.start_time >= str(datetime.now()), shows))
    upcoming_shows_count = len(upcoming_shows)
    data = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "image_link": artist.image_link,
        "past_shows": list(map(show_to_json_venue, past_shows)),
        "upcoming_shows": list(map(show_to_json_venue, upcoming_shows)),
        "past_shows_count": past_shows_count,
        "upcoming_shows_count": upcoming_shows_count,
    }
    # Redirect with data.
    return render_template('pages/show_artist.html', artist=data)


#  Update
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    # Get artist.
    artist = Artist.query.get(artist_id)
    # Populate form with fields from artist with ID <artist_id>.   
    artist = {
        "id": artist_id,
        "name": artist.name,
        "genres": artist.genres.split(','),
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
    }
    # Redirect with data.
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    # Edit changes
    artist.name = request.form.get('name', '')
    artist.city = request.form.get('city', '')
    artist.state = request.form.get('state', '')
    artist.phone = request.form.get('phone', '')
    artist.genres = request.form.get('genres', '')
    artist.facebook_link = request.form.get('facebook_link', '')
    # commit changes
    db.session.commit()
    # Redirect with data.
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # Get venue.
    venue = Venue.query.get(venue_id)
    # Populate form with values from venue with ID <venue_id>
    venue = {
        "id": venue_id,
        "name": venue.name,
        "genres": venue.genres.split(','),
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
    }
    # Redirect with data.
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    # Edit changes
    venue.name = request.form.get('name', '')
    venue.city = request.form.get('city', '')
    venue.state = request.form.get('state', '')
    venue.phone = request.form.get('phone', '')
    venue.address = request.form.get('address', '')
    venue.genres = request.form.get('genres', '')
    venue.facebook_link = request.form.get('facebook_link', '')
    # commit changes
    db.session.commit()
    # Redirect with data.
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
   
    # TODO: modify data to be the data object returned from db insertion
    try:
        # Get form data.
        name = request.form.get('name', '')
        city = request.form.get('city', '')
        state = request.form.get('state', '')
        phone = request.form.get('phone', '')
        genres = request.form.get('genres', '')
        facebook_link = request.form.get('facebook_link', '')
        # Create new Artist object, then add it.
        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link)
        db.session.add(artist)
        # Commit changes.
        db.session.commit()
        # on successful db insert, flash success.
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        
    except:
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' + request.form.get('name', '') + ' could not be listed.')
    finally:
        db.session.close()
    
    # Redirect with data.
    return render_template('pages/home.html')

#  Shows

def show_to_json(show):
    venue = Venue.query.get(show.venue_id)
    artist = Artist.query.get(show.artist_id)
    return {
        "venue_id": show.venue_id,
        "venue_name": venue.name,
        "artist_id": show.artist_id,
        "artist_name": artist.name,
        "artist_image_link": artist.image_link,
        "start_time": show.start_time,
    }
   
    
@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # Replace with real venues data.
    shows = Show.query.all()
    data = list(map(lambda show: show_to_json(show), shows))
    # Redirect with data.
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        # Get form data.
        venue_id = request.form['venue_id']
        artist_id = request.form['artist_id']
        start_time = request.form['start_time'] 
        show = Show(venue_id=venue_id, artist_id=artist_id, start_time=start_time)
        # Insert new Show.
        db.session.add(show)
        # Commit changes.
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
        
    except:
        db.session.rollback()
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Show could not be listed.')
    finally:
        db.session.close()

    # Redirect with data.
    return render_template('pages/home.html')    


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


# Launch.

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
