import React, { Component } from "react";

export default class NavigationBar extends Component {
    constructor(props) {
      super(props);      
      this.handleLogout = this.handleLogout.bind(this);
    }

    componentDidMount(){
        fetch('http://127.0.0.1:8000/api_rfront/user_is_logged')
        .then(results => {      
            return results.json();
        }).then(data => {      
            this.setState({ logged: data.logged });      
        });       
    }

    handleLogout() {
        fetch('http://127.0.0.1:8000/api_rfront/ajax_logout',{
            method: 'POST',
            body: JSON.stringify({}),
        }).then(results => {      
            return results.json();
        }).then(data => {      
            window.location.reload(false);
        });
    }
  
    render() {
      return (        
            <nav className="navbar navbar-expand-lg bg-light">
            <div className="container-fluid">
            <a className="navbar-brand" href="#">Mosquito Alert validation</a>
            <div className="collapse navbar-collapse" id="navbarSupportedContent">                
                <ul className="navbar-nav me-auto mb-2 mb-lg-0">
                    <li className="nav-item">
                        <div className="btn-group">
                            <input type="radio" className="btn-check" name="status" id="option1"></input>                            
                            <label className="btn btn-outline-primary"><i className="fa-solid fa-clock"></i> { this.props.n_pending }</label>
                            <input type="radio" className="btn-check" name="status" id="option2"></input>                                                                
                            <label className="btn btn-outline-primary"><i className="fa-solid fa-square-check"></i> { this.props.n_complete }</label>                            
                        </div>
                    </li>
                    <li className="nav-item">
                        <button className="btn btn-primary btn-success">Next page</button>
                        <button className="btn btn-primary btn-success">Previous page</button>
                    </li>
                    
                </ul>
                <ul className="navbar-nav mr-5">
                    <li className="nav-item">
                        <button className="btn btn-primary btn-secondary" onClick={this.handleLogout}>Logout</button>
                    </li>
                </ul>
            </div>
            </div>
            </nav>
      );
    }
}