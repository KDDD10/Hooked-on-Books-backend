from flask import Blueprint, request, jsonify
from app import db
from app.models.book import Book
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import re

bp = Blueprint('books', __name__)



@bp.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400
    
    # Validate required fields
    required_fields = ['title', 'author', 'publication_date']
    for field in required_fields:
        if field not in data:
            return jsonify({"message": f"Missing required field: {field}"}), 400


    current_user_id = get_jwt_identity()
    
   
    try:
        new_book = Book(
            title=data['title'],
            author=data['author'],
            cover_image_url=data.get('cover_image_url'),
            description=data.get('description'),
            publication_date=datetime.strptime(data['publication_date'], '%Y-%m-%d').date(),
            genres=','.join(data.get('genres', [])),
            affiliate_link=data.get('affiliate_link'),
            user_id=current_user_id
        )
        
        db.session.add(new_book)
        db.session.commit()
        
        return jsonify({
            "message": "Book added successfully",
            "book_id": new_book.id
        }), 201
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        db.session.rollback()
        error_message = str(e)
        if "StringDataRightTruncation" in error_message:
            return jsonify({"message": "One or more fields exceed the maximum allowed length"}), 400
        return jsonify({"message": f"An unexpected error occurred: {error_message}"}), 500


@bp.route('/books', methods=['GET'])
def get_all_books():
    books = Book.query.all()
    return jsonify([{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover_image_url": book.cover_image_url,
        "publication_date": book.publication_date.isoformat(),
        "genres": book.genres.split(','),
        "user_id": book.user_id
    } for book in books]), 200

@bp.route('/books/user/<int:user_id>', methods=['GET'])
def get_books_by_user(user_id):
    books = Book.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover_image_url": book.cover_image_url,
        "publication_date": book.publication_date.isoformat(),
        "genres": book.genres.split(','),
    } for book in books]), 200

@bp.route('/books/<int:book_id>', methods=['GET'])
def get_single_book(book_id):
    book = Book.query.get_or_404(book_id)
    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover_image_url": book.cover_image_url,
        "description": book.description,
        "publication_date": book.publication_date.isoformat(),
        "genres": book.genres.split(','),
        "affiliate_link": book.affiliate_link,
        "user_id": book.user_id
    }), 200

@bp.route('/books/<int:book_id>', methods=['PUT'])
@jwt_required()
def update_book(book_id):
    book = Book.query.get_or_404(book_id)
    current_user_id = get_jwt_identity()
    
    if book.user_id != current_user_id:
        return jsonify({"message": "You don't have permission to update this book"}), 403
    
    data = request.get_json()
    
    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    book.cover_image_url = data.get('cover_image_url', book.cover_image_url)
    book.description = data.get('description', book.description)
    book.publication_date = datetime.strptime(data.get('publication_date', book.publication_date.isoformat()), '%Y-%m-%d').date()
    book.genres = ','.join(data.get('genres', book.genres.split(',')))
    book.affiliate_link = data.get('affiliate_link', book.affiliate_link)
    
    db.session.commit()
    
    return jsonify({"message": "Book updated successfully"}), 200

@bp.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    current_user_id = get_jwt_identity()
    
    if book.user_id != current_user_id:
        return jsonify({"message": "You don't have permission to delete this book"}), 403
    
    db.session.delete(book)
    db.session.commit()
    
    return jsonify({"message": "Book deleted successfully"}), 200        