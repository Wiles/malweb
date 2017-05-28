const graphql = require('graphql');
const { Staff, StaffType } = require('../Staff');
const { Anime, AnimeType } = require('../Anime');

module.exports = new graphql.GraphQLObjectType({
  name: 'User',
  fields: () => ({
    id: {
      type: graphql.GraphQLInt
    },
    name: {
      type: graphql.GraphQLString
    },
    staffList: {
      type: new graphql.GraphQLList(StaffType),
      resolve: ({ id }, params, req, { rootValue: { db } }) =>
        Staff.findByUser(db, id, 25)
    },
    animeList: {
      type: new graphql.GraphQLList(AnimeType),
      resolve: ({ id }, params, req, { rootValue: { db } }) =>
        Anime.findByUser(db, id, 25)
    }
  })
});
