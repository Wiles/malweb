const graphql = require('graphql');

const UserType = require('./UserType');
const User = require('./UserSchema');

module.exports = {
  user: {
    type: UserType,
    args: {
      name: {
        type: new graphql.GraphQLNonNull(graphql.GraphQLString)
      }
    },
    resolve({ db }, { name }) {
      return User.findByName(db, name);
    }
  }
};
