require('dotenv').config()

const config = {
  graphql: {
    port: process.env.GRAPHQL_PORT
  },
  neo4j_bolt_url: process.env.NEO4J_BOLT_URL
};

module.exports = config;
