/**
 *Submitted for verification at Etherscan.io on 2018-11-27
*/

pragma solidity ^0.4.24;

contract owned {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    function transferOwnership(address newOwner) onlyOwner public {
        owner = newOwner;
    }
}

contract logContract is owned {

    /* Struct for one app */
    struct App {
        bool isActive;
        address[] authAdmin;
    }

    address[] admin;
    mapping(string => App) apps;

    /** constructor */
    constructor() public {
        admin.push(owner);
    }


    // admin related
    function isAdmin(address _address) public view returns(int idx) {
        for (uint i = 0; i<=admin.length-1; i++){
            if(_address == admin[i]) {
                return int(i);
            }
        }
        return -1;
    }

    modifier onlyAdmin {
        require(isAdmin(msg.sender) != -1);
        _;
    }

    function addAdmin(address _address) onlyAdmin public {
        // _address already in admin
        if(isAdmin(_address) != -1) {
            return;
        }
        admin.push(_address);
    }

    function delAdmin(address _address) onlyOwner public {
        int idx = isAdmin(_address);
        // _address is not admin
        if(idx == -1) {
            return;
        }
        uint index = uint(idx);
        if (index >= admin.length) {
            return;
        }
        admin[index] = admin[admin.length-1];
        delete admin[admin.length-1];
        admin.length--;
    }


    function getAllAdmin() public view returns(address[] list) {
        list = admin;
    }

    // app related
    function authApp(string appId) onlyAdmin public {
        apps[appId].authAdmin.push(msg.sender);
        if(apps[appId].authAdmin.length >= 2) {
            apps[appId].isActive = true;
        }
    }

    function addApp(string appId) onlyAdmin public{
        apps[appId] = App({isActive:false, authAdmin: new address[](0)});
    }

    function getAppStatus(string appId) public view returns(bool status) {
        status = apps[appId].isActive;
    }
}