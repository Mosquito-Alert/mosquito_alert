import React, { Component } from "react";
import { createRoot } from 'react-dom/client';
import HomePage from "./HomePage";
import NavigationBar from "./NavigationBar";

export default class App extends Component {    
  
  constructor(props) {
    super(props);
    this.state = {
        my_reports : [],
        loaded: false
    };
  }
  
  componentDidMount(){
    fetch('http://127.0.0.1:8000/api/all_reports_paginated/?format=json&page_size=20')
    .then(results => {
      return results.json();
    }).then(data => {      
      this.setState({ my_reports: data.results, loaded: true });
    });
  }

  render() {
    const { loaded, my_reports } = this.state;
    var n_reports = 0;
    if(my_reports != null){
      n_reports = my_reports.length;
    }
    if(!loaded) return (
        <div><h3>Loading data please wait...</h3></div>
    );
    return (      
        <NavigationBar n_complete={ n_reports } n_pending="0"/>
    );
  }
}

const appDiv = document.getElementById("app");
const root = createRoot(appDiv);

root.render(<App/>);