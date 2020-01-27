*** Settings ***
Library         REST    http://127.0.0.1:5000/api/v1/

*** Test Cases ***
GET points in geo.json format from Germany from 2019-09-13 with limit and offset
    GET         geo.json?country=DE&begin=2019-09-13&end=2019-09-14&limit=10&offset=10
    Object      $
    String      $.type      FeatureCollection
    Array       $.features


GET averages from geoframe from 2019-09-13
    GET         average.json?geoframe=15,8,-10,0&begin=2019-09-13&end=2019-09-14
    Array       $
    Object      $[0]
    Number      $[0].average
    String      $[0].start
    String      $[0].end


Get statistics from polygon from 2019-09-13
    GET         statistics.json?polygon=15,8,15,0,-10,0,-10,8,15,8&begin=2019-09-13&end=2019-09-14
    Array       $
    Object      $[0]
    Object      $[*].time       required=["interval_start", "max", "min"]
    Object      $[*].value      required=["average", "count", "max", "min", "standard deviation"]
