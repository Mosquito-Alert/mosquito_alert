import React, { Component } from "react";

import {
  BrowserRouter as Router,  
  Routes,
  Route,
  BrowserRouter,
  Link,
  Redirect,
} from "react-router-dom";

export default class HomePage extends Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (        
        <p>This is the home page</p>            
    );
  }
}