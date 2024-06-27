from flask import Blueprint, request, flash, render_template

bp = Blueprint('page', __name__)

@bp.route('/about')
def about():
    return render_template('page/about.html')

@bp.route('/const')
def const():
    return render_template('page/const.html')

@bp.route('/organ')
def organ():
    return render_template('page/organ.html')

@bp.route('/gal')
def gal():
    return render_template('page/gal.html')


