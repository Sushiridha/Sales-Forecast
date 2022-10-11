from json import load
import os
from flask import Flask, render_template, request as req, send_file
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import pandas as pd
import numpy as np
import seaborn as sns
sns.set_style('whitegrid')
from itertools import cycle
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")
from sklearn.preprocessing import MinMaxScaler
from keras.models import load_model


app = Flask(__name__)
cors = CORS(app)

@app.post("/data")
@cross_origin()
def getData():
    f = req.files['file']
    f.save(secure_filename(f.filename))
    fileName = os.path.abspath(f.filename)
    global df
    df = pd.read_csv(fileName,index_col='Date')
    
    
    return {
        "Message":"Sucess"
    }

@app.post("/predict")
def predictData():
    timeperiod = req.json['timeperiod']
    print(timeperiod)
    df.reset_index(inplace=True)
    df.columns=['Date','Sales']
    closedf = df.copy()
    close_stock = df.copy()
    closedf.drop(['Date'],axis=1,inplace=True)

    scaler=MinMaxScaler(feature_range=(0,1))
    closedf=scaler.fit_transform(np.array(closedf).reshape(-1,1))

    training_size=int(len(closedf)*0.70)
    test_size=len(closedf)-training_size
    train_data,test_data=closedf[0:training_size,:],closedf[training_size:len(closedf),:1]
  
    def create_dataset(dataset, time_step=1):
        dataX, dataY = [], []
        for i in range(len(dataset)-time_step-1):
            a = dataset[i:(i+time_step), 0]   ###i=0, 0,1,2,3-----99   100 
            dataX.append(a)
            dataY.append(dataset[i + time_step, 0])
        return np.array(dataX), np.array(dataY)
    time_step =int(timeperiod)
    X_train, y_train = create_dataset(train_data, time_step)
    X_test, y_test = create_dataset(test_data, time_step)

    X_train =X_train.reshape(X_train.shape[0],X_train.shape[1] , 1)
    X_test = X_test.reshape(X_test.shape[0],X_test.shape[1] , 1)

    model = load_model('Model\LSTM.h5')
    train_predict=model.predict(X_train)
    test_predict=model.predict(X_test)
    
    train_predict = scaler.inverse_transform(train_predict)
    test_predict = scaler.inverse_transform(test_predict)
    original_ytrain = scaler.inverse_transform(y_train.reshape(-1,1)) 
    original_ytest = scaler.inverse_transform(y_test.reshape(-1,1))
    look_back=time_step
    trainPredictPlot = np.empty_like(closedf)
    trainPredictPlot[:, :] = np.nan
    trainPredictPlot[look_back:len(train_predict)+look_back, :] = train_predict


    # shift test predictions for plotting
    testPredictPlot = np.empty_like(closedf)
    testPredictPlot[:, :] = np.nan
    testPredictPlot[len(train_predict)+(look_back*2)+1:len(closedf)-1, :] = test_predict
 

    names = cycle(['Original sales price','Train predicted sales price','Test predicted sales price']) ##legend plotly


    plotdf = pd.DataFrame({'date': close_stock['Date'],
                        'original_sales': close_stock['Sales'],
                        'train_predicted_sales': trainPredictPlot.reshape(1,-1)[0].tolist(),
                        'test_predicted_sales': testPredictPlot.reshape(1,-1)[0].tolist()})

    fig = px.line(plotdf,x=plotdf['date'], y=[plotdf['original_sales'],plotdf['train_predicted_sales'],
                                            plotdf['test_predicted_sales']],
                labels={'value':'Sales price','date': 'Date'})
    fig.update_layout(title_text='Original Sales vs Predicted Sales',
                    plot_bgcolor='white', font_size=15, font_color='black', legend_title_text='Sales')
    fig.for_each_trace(lambda t:  t.update(name = next(names)))

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    fig.write_image("Plot.png")

    return {
        "Message":"Sucess"
    }


@app.get("/results")
def results():
    return send_file("Plot.png")


app.run()