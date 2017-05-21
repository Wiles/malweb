const graphql = require('graphql');

const StaffType = require('./StaffType');
const Staff = require('./StaffSchema');

module.exports = {
  staff: {
    type: StaffType,
    args: {
      id: {
        type: new graphql.GraphQLNonNull(graphql.GraphQLInt)
      },
      user: {
        type: new graphql.GraphQLNonNull(graphql.GraphQLInt)
      }
    },
    resolve({ db }, { id, user }) {
      return Staff.findById(db, id, user);
    }
  }
};
