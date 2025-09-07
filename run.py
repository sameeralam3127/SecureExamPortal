from app import create_app, db
import os

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create database folder if not exists
        if not os.path.exists('data'):
            os.makedirs('data')
        
        db.create_all()
    
    app.run(debug=True, port=5001)
