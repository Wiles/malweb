const graphql = require('graphql');
const User = require('./User');
const Staff = require('./Staff');
const Anime = require('./Anime');

const RootQuery = new graphql.GraphQLObjectType({
  name: 'Query',
  fields: () => ({
    user: User.UserQueries.user,
    staff: Staff.StaffQueries.staff,
    anime: Anime.AnimeQueries.anime
  })
});

const schema = new graphql.GraphQLSchema({
  query: RootQuery
});

module.exports = schema;
