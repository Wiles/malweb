const path = require('path');
const fs = require('fs');
const { graphql } = require('graphql');
const chalk = require('chalk');
const { introspectionQuery, printSchema } = require('graphql/utilities');
const schema = require('../data/models');

const jsonFile = path.join(__dirname, 'schema.json');
const graphQLFile = path.join(__dirname, 'schema.graphql');

async function updateSchema() {
  try {
    const json = await graphql(schema, introspectionQuery);
    fs.writeFileSync(jsonFile, JSON.stringify(json, null, '  '));
    fs.writeFileSync(graphQLFile, printSchema(schema));
    console.info(chalk.green('Schema has been regenerated'));
  } catch (err) {
    console.error(chalk.red(err.stack));
  }
}

// Run the function directly, if it's called from the command line
if (!module.parent) updateSchema();

export default updateSchema;
