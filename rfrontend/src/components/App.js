import React, { Component } from "react";
import { createRoot } from 'react-dom/client';
import HomePage from "./HomePage";
import NavigationBar from "./NavigationBar";

export default class App extends Component {
  
  constructor(props) {
    super(props);
    /*
    this.state = {
        my_reports : [],
        loaded: false
    };
    */
    this.state = {      
      logged: false,
      loginSuccessful: true
    };
    this.handleSubmit = this.handleSubmit.bind(this);    
  }  

  handleSubmit(event) {
    var { uname, pass } = document.forms[0];    
    event.preventDefault();
    const data = {
      'username': uname.value,
      'password': pass.value
    }
    fetch('http://127.0.0.1:8000/api_rfront/ajax_login',{
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })
    .then(results => {      
      return results.json();
    }).then(data => {      
      this.setState({ logged: data.success, loginSuccessful: data.success });
    });
  }
  
  componentDidMount(){
    fetch('http://127.0.0.1:8000/api_rfront/user_is_logged')
    .then(results => {      
      return results.json();
    }).then(data => {      
      this.setState({ logged: data.logged });      
    });
    /*
    fetch('http://127.0.0.1:8000/api/all_reports_paginated/?format=json&page_size=20')
    .then(results => {
      return results.json();
    }).then(data => {      
      this.setState({ my_reports: data.results, loaded: true });
    });
    */
  }

  render() {
    /*const { loaded, my_reports } = this.state;
    var n_reports = 0;
    if(my_reports != null){
      n_reports = my_reports.length;
    }
    if(!loaded) return (
        <div><h3>Loading data please wait...</h3></div>
    );
    return (      
        <NavigationBar n_complete={ n_reports } n_pending="0"/>
    );*/
    const { logged,loginSuccessful } = this.state;
    let errorMessage;
    if(!loginSuccessful){
      errorMessage = <div><p className="text-danger">Incorrect username or password, try again...</p></div>;
    }
    if(!logged){ 
      return (      
        <div className="login-form">
            <form onSubmit={this.handleSubmit}>
                <div className="mb-3">
                  <label className="form-label">Username </label>
                  <input className="form-control" type="text" name="uname" required />                        
                </div>
                <div className="mb-3">
                  <label className="form-label">Password </label>
                  <input className="form-control" type="password" name="pass" required />
                </div>
                <div className="mb-3">
                  <button type="submit" className="btn btn-primary mb-3">Submit</button>
                </div>                                            
                {errorMessage}
            </form>
        </div>
      )
    } else {
      return (      
        <div>
          <NavigationBar n_complete="0" n_pending="0" />        
        </div>      
      )
    }    
  }
}

const appDiv = document.getElementById("app");
const root = createRoot(appDiv);

root.render(<App/>);