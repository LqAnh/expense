Docker for MongoDB

    docker run --name mongodb -p 27017:27017 -d mongodb/mongodb-community-server:latest

Start back-end

    uvicorn main:app --reload  

Start front-end

    streamlit run app.py