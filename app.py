import psycopg2
import pandas as pd
import numpy as np
from flask import Flask, jsonify, request
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import create_engine
import plotly.graph_objects as go
import base64
from io import BytesIO
from flask_cors import CORS

app = Flask(__name__)

CORS(app)


@app.route('/')
def home():
    return "Welcome to the Flask App!"

# Database connection details
db_config = {
    'host': 'localhost',
    'database': 'recipe_db',
    'user': 'postgres',
    'password': 'Mo!h6?35',
    'port': '5432'
}

# Establish connection to PostgreSQL
conn = psycopg2.connect(**db_config)

# Retrieve recipes and ingredients data
recipe_query = """
SELECT r.name, r.description, n.calories, n.total_fat, n.protein, n.carbs, 
       i.ingredient_text, d.instruction_text
FROM recipes r
JOIN nutrition_facts n ON r.recipe_id = n.recipe_id
JOIN ingredients i ON r.recipe_id = i.recipe_id
JOIN directions d ON r.recipe_id = d.recipe_id;
"""

# Load data into a DataFrame
recipes_df = pd.read_sql(recipe_query, conn)
#print(recipes_df.columns)

# Retrieve pre-saved embeddings
embedding_query = "SELECT name, embedding FROM recipe_embeddings;"
embeddings_df = pd.read_sql(embedding_query, conn)
conn.close()

# Decode embeddings into NumPy arrays
embeddings_df['embedding'] = embeddings_df['embedding'].apply(
    lambda x: np.frombuffer(bytes.fromhex(x[2:]), dtype=np.float32)
)

recipes_df['description'] = recipes_df['description'].fillna('').astype(str)
recipes_df['ingredient_text'] = recipes_df['ingredient_text'].fillna('').astype(str)
recipes_df['instruction_text'] = recipes_df['instruction_text'].fillna('').astype(str)

# Merge recipe data with embeddings
recipes_texts = recipes_df.groupby('name')['description'].apply(' '.join).reset_index()
recipes_texts = recipes_texts.merge(embeddings_df, on='name')

def create_nutritional_chart(nutrients):
    """
    Generate a bar chart for the nutritional breakdown and return as a base64 string.
    """
    labels = list(nutrients.keys())
    values = list(nutrients.values())

    fig = go.Figure(data=[go.Bar(x=labels, y=values, marker_color=['#FF9999', '#66B3FF', '#99FF99'])])
    fig.update_layout(
        title="Nutritional Breakdown",
        xaxis_title="Nutrient",
        yaxis_title="Amount (g)",
        template="plotly_white",
    )

    # Save the chart to a buffer as a base64 string
    buffer = BytesIO()
    fig.write_image(buffer, format="png")
    buffer.seek(0)
    base64_image = base64.b64encode(buffer.read()).decode("utf-8")
    buffer.close()
    return base64_image

@app.route("/recommend", methods=["POST"])
def recommend():
    """
    Endpoint to get recommendations based on user preferences.
    """
    user_input = request.json.get("preferences", "")
    if not user_input:
        return jsonify({"error": "Preferences not provided"}), 400

    # Generate embedding for user input
    model = SentenceTransformer('all-MiniLM-L6-v2')
    user_embedding = model.encode(user_input)

    # Calculate similarity scores
    recipes_texts['similarity'] = recipes_texts['embedding'].apply(
        lambda x: cosine_similarity([user_embedding], [x]).flatten()[0]
    )

    # Sort by similarity and return top N recommendations
    top_n = 5  # You can adjust this number as needed
    recommendations = recipes_texts.sort_values(by='similarity', ascending=False).head(top_n)

    # Add nutritional information and generate charts
    recommendations['chart'] = recommendations['name'].apply(
        lambda x: create_nutritional_chart(
            recipes_df[recipes_df['name'] == x].iloc[0][['calories', 'total_fat', 'protein', 'carbs']].to_dict()
        )
    )

    # Merge with descriptions and similarity for frontend
    recommendations['description'] = recommendations['name'].apply(
        lambda x: recipes_df[recipes_df['name'] == x].iloc[0]['description']
    )

    return jsonify({"recommendations": recommendations[['name', 'similarity', 'description', 'chart']].to_dict(orient='records')}), 200

if __name__ == "__main__":
    app.run(debug=True)