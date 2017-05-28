const {
  GraphQLObjectType,
  GraphQLInt,
  GraphQLString,
  GraphQLFloat,
  GraphQLList
} = require('graphql');

module.exports = new GraphQLObjectType({
  name: 'Staff',
  fields: () => {
    const { Anime, AnimeType } = require('../Anime'); // eslint-disable-line global-require
    return {
      id: {
        type: GraphQLInt
      },
      name: {
        type: GraphQLString
      },
      metascore: {
        type: GraphQLFloat
      },
      position: {
        type: new GraphQLList(GraphQLString)
      },
      animeList: {
        type: new GraphQLList(AnimeType),
        resolve: ({ id, userId }, params, req, { rootValue: { db } }) =>
          Anime.findByStaff(db, id, userId)
      }
    };
  }
});
