var express = require('express');
var stylus = require('stylus');
var bodyParser = require('body-parser');


module.exports = function(app, config) {
  function compile(str, path) {
    return stylus(str).set('filename', path);
  }

  app.locals.pretty = true;
  app.set('views', config.rootPath + '/server/views');
  app.set('view engine', 'jade');


  app.use(bodyParser.json());
  app.use(bodyParser.urlencoded({
    extended: true
  }));
  app.use(stylus.middleware(
    {
      src: config.rootPath + '/public',
      compile: compile
    }
  ));
  app.use(express.static(config.rootPath + '/public/'));
};