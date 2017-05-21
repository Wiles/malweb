const graphql = require('graphql');

const AnimeType = require('./AnimeType');
const Anime = require('./AnimeSchema');

module.exports = {
  anime: {
    type: AnimeType,
    args: {
      id: {
        type: new graphql.GraphQLNonNull(graphql.GraphQLInt)
      },
      user: {
        type: new graphql.GraphQLNonNull(graphql.GraphQLInt)
      }
    },
    resolve({ db }, { id, user }) {
      return Anime.findById(db, id, user);
    }
  }
};
