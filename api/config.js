require('dotenv').config();

const config = {
  graphql: {
    port: process.env.GRAPHQL_PORT
  },
  neo4j_bolt_url: process.env.NEO4J_BOLT_URL,
  winston_level: process.env.WINSTON_LEVEL
};

module.exports = config;
