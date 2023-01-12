import React, { Component } from "react";

export default class NavigationBar extends Component {
    constructor(props) {
      super(props);
    }
  
    render() {
      return (        
            <nav className="navbar navbar-expand-lg bg-light">
            <div className="container-fluid">
            <a className="navbar-brand" href="#">Mosquito Alert validation</a>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">                
                <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                    <li className="nav-item">
                        <div className="btn-group" id="status_grp" data-toggle="buttons">
                                <label className="btn btn-primary btn-sm navbar-btn" data-toggle="tooltip" data-placement="bottom" title="Pending" id="pending_btn">
                                    <input type="radio" name="status"></input>
                                    <i className="fa-solid fa-clock"></i>                                    
                                    <span className="badge">{ this.props.n_pending }</span>                                        
                                </label>
                                <label className="btn btn-primary btn-sm navbar-btn" data-toggle="tooltip" data-placement="bottom" title="Complete" id="complete_btn">
                                    <input type="radio" name="status"></input>
                                    <i className="fa-solid fa-square-check"></i>                                    
                                    <span className="badge">{ this.props.n_complete }</span>                                        
                                </label>
                        </div>
                    </li>
                    <li className="nav-item">
                        <button className="btn btn-primary btn-success">Next page</button>
                        <button className="btn btn-primary btn-success">Previous page</button>
                    </li>
                </ul>                
            </div>
            </div>
            </nav>
      );
    }
}