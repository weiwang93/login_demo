/**
 *Submitted for verification at Etherscan.io on 2018-11-27
*/

pragma solidity ^0.4.26;
pragma experimental ABIEncoderV2;

contract owned {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner {
        require(msg.sender == owner, "only owner can call this function!");
        _;
    }

    function transferOwnership(address newOwner) onlyOwner public {
        owner = newOwner;
    }
}

library StringUtils {
    /// @dev Does a byte-by-byte lexicographical comparison of two strings.
    /// @return a negative number if `_a` is smaller, zero if they are equal
    /// and a positive numbe if `_b` is smaller.
    function compare(string _a, string _b) internal returns (int) {
        bytes memory a = bytes(_a);
        bytes memory b = bytes(_b);
        uint minLength = a.length;
        if (b.length < minLength) minLength = b.length;
        //@todo unroll the loop into increments of 32 and do full 32 byte comparisons
        for (uint i = 0; i < minLength; i ++)
            if (a[i] < b[i])
                return -1;
            else if (a[i] > b[i])
                return 1;
        if (a.length < b.length)
            return -1;
        else if (a.length > b.length)
            return 1;
        else
            return 0;
    }
    /// @dev Compares two strings and returns true iff they are equal.
    function equal(string _a, string _b) internal returns (bool) {
        return compare(_a, _b) == 0;
    }
}

library addressUtils {
    /// return index if _address in addressList
    /// return -1 if _address not in addressList
    function getAddressIndex(address _address, address[] addressList) internal returns (int){
        /// if addressList is empty
        if(addressList.length == 0) {
            return -1;
        }
        for (uint i = 0; i <= addressList.length-1; i++){
            if(_address == addressList[uint(i)]) {
                return int(i);
            }
        }
        return -1;
    }
}

contract loginContract is owned {
    /* Struct for one app */
    struct App {
        bool isActive;
        address[] authAdmin;
    }

    address[] adminList ;
    mapping(string => App) appList;
    string[] appNameList;
    string[] authedAppNameList;

    /** constructor */
    constructor() public {
        adminList.push(owner);
    }

    // admin related
    modifier onlyAdmin {
        require(addressUtils.getAddressIndex(msg.sender, adminList) != -1, "only admin can call this function!");
        _;
    }

    function addAdmin(address _address) onlyAdmin public {
        // _address already in admin
        if(addressUtils.getAddressIndex(_address, adminList) != -1) {
            return;
        }
        adminList.push(_address);
    }

    function deleteAdmin(address _address) onlyOwner public returns(address[]){
        require (_address != owner, "can not DELETE owner");
        int idx = addressUtils.getAddressIndex(_address, adminList);
        // _address is not admin
        if(idx == -1) {
            return;
        }
        uint index = uint(idx);
        if (index >= adminList.length) {
            return;
        }
        adminList[index] = adminList[adminList.length-1];
        delete adminList[adminList.length-1];
        adminList.length--;
        return adminList;
    }

    function getAllAdmin() public view returns(address[]) {
        return adminList;
    }

    function getAdminUum() public view returns(uint) {
        return adminList.length;
    }

    // app related
    function isAppExists(string appName) public view returns(bool) {
        if(appNameList.length == 0) {
            return false;
        }
        for (uint i = 0; i <= appNameList.length-1; i++){
            if(StringUtils.equal(appName, appNameList[i])) {
                return true;
            }
        }
        return false;
    }

    function addApp(string appName) public{
        require(!isAppExists(appName), "app already exists");
        appList[appName] = App({isActive:false, authAdmin: new address[](0)});
        appNameList.push(appName);
    }

    function authorizeApp(string appName) onlyAdmin public{
        require(isAppExists(appName), "app not exists");
        require(addressUtils.getAddressIndex(msg.sender, appList[appName].authAdmin) == -1, "You already authorize this app!");
        appList[appName].authAdmin.push(msg.sender);
        if(appList[appName].authAdmin.length >= 2) {
            appList[appName].isActive = true;
            authedAppNameList.push(appName);
        }
    }

    function prohibitApp(string appName) onlyAdmin public{
        require(isAppExists(appName), "app not exists");
        appList[appName].isActive = false;
        delete appList[appName].authAdmin;
        for(uint i = 0; i < authedAppNameList.length; i++) {
            if(StringUtils.equal(appName, authedAppNameList[i])) {
                authedAppNameList[i] = authedAppNameList[authedAppNameList.length - 1];
                break;
            }
        }
        delete authedAppNameList[authedAppNameList.length-1];
        authedAppNameList.length--;
    }

    function getAppStatus(string appName) public view returns(App) {
        return appList[appName];
    }

    function getAuthenticatedApp() public view returns(string[]) {
        return authedAppNameList;
    }

    function getAllApp() public view returns(string[]) {
        return appNameList;
    }
}