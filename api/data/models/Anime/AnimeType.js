const {
  GraphQLObjectType,
  GraphQLInt,
  GraphQLString,
  GraphQLFloat,
  GraphQLList
} = require('graphql');

const AnimeType = new GraphQLObjectType({
  name: 'Anime',
  fields: () => {
    const { Staff, StaffType } = require('../Staff'); // eslint-disable-line global-require
    return {
      id: {
        type: GraphQLInt
      },
      name: {
        type: GraphQLString
      },
      score: {
        type: GraphQLFloat
      },
      metascore: {
        type: GraphQLFloat
      },
      staffList: {
        type: new GraphQLList(StaffType),
        resolve: ({ id, userId }, params, req, { rootValue: { db } }) =>
          Staff.findByAnime(db, id, userId)
      }
    };
  }
});

module.exports = AnimeType;
