from flask import Blueprint, request, jsonify
from app import db
from app.models.review import Review
from app.models.book import Book
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('reviews', __name__)

@bp.route('/books/<int:book_id>/reviews', methods=['POST'])
@jwt_required()
def add_review(book_id):
    data = request.get_json()
    current_user_id = get_jwt_identity()

    book = Book.query.get_or_404(book_id)

    if 'rating' not in data or not isinstance(data['rating'], int) or data['rating'] < 1 or data['rating'] > 5:
        return jsonify({"message": "Invalid rating. Must be an integer between 1 and 5."}), 400

    new_review = Review(
        book_id=book_id,
        user_id=current_user_id,
        rating=data['rating'],
        review_text=data.get('review_text', '')
    )

    db.session.add(new_review)
    db.session.commit()

    return jsonify({"message": "Review added successfully", "review_id": new_review.id}), 201

@bp.route('/books/<int:book_id>/reviews', methods=['GET'])
def get_book_reviews(book_id):
    Book.query.get_or_404(book_id)  # Check if book exists
    reviews = Review.query.filter_by(book_id=book_id).all()
    return jsonify([{
        "id": review.id,
        "user_id": review.user_id,
        "rating": review.rating,
        "review_text": review.review_text,
        "date_posted": review.date_posted.isoformat(),
        "upvotes_count": review.upvotes_count
    } for review in reviews]), 200

@bp.route('/reviews/<int:review_id>', methods=['GET'])
def get_single_review(review_id):
    review = Review.query.get_or_404(review_id)
    return jsonify({
        "id": review.id,
        "book_id": review.book_id,
        "user_id": review.user_id,
        "rating": review.rating,
        "review_text": review.review_text,
        "date_posted": review.date_posted.isoformat(),
        "upvotes_count": review.upvotes_count
    }), 200

@bp.route('/reviews/<int:review_id>', methods=['PUT'])
@jwt_required()
def update_review(review_id):
    review = Review.query.get_or_404(review_id)
    current_user_id = get_jwt_identity()

    if review.user_id != current_user_id:
        return jsonify({"message": "You don't have permission to update this review"}), 403

    data = request.get_json()

    if 'rating' in data:
        if not isinstance(data['rating'], int) or data['rating'] < 1 or data['rating'] > 5:
            return jsonify({"message": "Invalid rating. Must be an integer between 1 and 5."}), 400
        review.rating = data['rating']

    if 'review_text' in data:
        review.review_text = data['review_text']

    db.session.commit()

    return jsonify({"message": "Review updated successfully"}), 200

@bp.route('/reviews/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    current_user_id = get_jwt_identity()

    if review.user_id != current_user_id:
        return jsonify({"message": "You don't have permission to delete this review"}), 403

    db.session.delete(review)
    db.session.commit()

    return jsonify({"message": "Review deleted successfully"}), 200

@bp.route('/reviews/<int:review_id>/upvote', methods=['POST'])
@jwt_required()
def upvote_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.upvotes_count += 1
    db.session.commit()

    return jsonify({"message": "Review upvoted successfully", "new_upvote_count": review.upvotes_count}), 200