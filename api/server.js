const http = require('http');
const express = require('express');
const graphQLHTTP = require('express-graphql');
const path = require('path');
const { v1 } = require('neo4j-driver');
const winston = require('winston');

const config = require('./config');
const schema = require('./data/models');

winston.level = config.winston_level;

const app = express();

const db = v1.driver(config.neo4j_bolt_url);

app.use('/graphql', graphQLHTTP({
  schema,
  rootValue: { db },
  pretty: true,
  graphiql: true
}));

app.use('/axios.min.js', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/axios.min.js'));
});

app.use('/sorttable.js', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/sorttable.js'));
});

app.use('/anime', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/anime.html'));
});

app.use('/staff', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/staff.html'));
});

app.use('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'views/index.html'));
});

process.on('uncaughtException', (err) => {
  winston.error(
    `Uncaught Exception: Error - ${err.stack || err.message}`
  );
});

process.on('unhandledRejection', (reason, promise) => {
  winston.error(
    `Unhandled Rejection: Promise - ${promise} Reaseon - ${reason}`
  );
});

const httpServer = http.createServer(app);

httpServer.listen(config.graphql.port, () => {
  winston.info(
    `GraphQL HTTP server is now running on http://localhost:${config.graphql.port}`
  );
});
