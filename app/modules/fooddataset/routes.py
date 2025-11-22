from flask import render_template
from app.modules.fooddataset import fooddataset_bp


@fooddataset_bp.route('/fooddataset', methods=['GET'])
def index():
    return render_template('fooddataset/index.html')
