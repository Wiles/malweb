const graphql = require('graphql');

module.exports = new graphql.GraphQLObjectType({
  name: 'Staff',
  fields: () => {
    const { Anime, AnimeType } = require('../Anime'); // eslint-disable-line global-require
    return {
      id: {
        type: graphql.GraphQLInt
      },
      name: {
        type: graphql.GraphQLString
      },
      metascore: {
        type: graphql.GraphQLFloat
      },
      animeList: {
        type: new graphql.GraphQLList(AnimeType),
        resolve: ({ id, userId }, params, req, { rootValue: { db } }) =>
          Anime.findByStaff(db, id, userId)
      }
    };
  }
});
