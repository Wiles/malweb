const findByUser = (server, userId, minCount, limit) => {
  console.log('anime.findByUser');
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (user:User {id: {userId}})-[meta:META_SCORED]->(anime:Anime)
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      RETURN
        anime.id as id,
        anime.name as name,
        meta.value as metascore,
        rating.score as score
      ORDER BY metascore DESC
      LIMIT {limit}
    `, {
      userId,
      minCount,
      limit
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
          score: r.get('score'),
          metascore: r.get('metascore')
        }
      })
      resolve(r);
    })
    .catch((err) => {
      reject(err);
    })
  });
};

const findById = (server, animeId, userId) => {
  console.log('anime.findById');
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (anime:Anime {id: {animeId}})
      OPTIONAL MATCH (user:User {id: {userId}})-[meta:META_SCORED]->(anime)
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      RETURN
        anime.id as id,
        anime.name as name,
        meta.value as metascore,
        meta.count as count,
        rating.score as score
      ORDER BY metascore DESC
      LIMIT 10
    `, {
      animeId,
      userId
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
          score: r.get('score'),
          metascore: r.get('metascore'),
          userId
        }
      })

      resolve(r[0]);
    })
    .catch((err) => {
      reject(err);
    })
  });
};

const findByStaff = (server, staffId, userId) => {
  console.log('anime.findByStaff');
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (:Staff {id: {staffId}})-[:WorkedOn]->(anime:Anime)
      MATCH (user:User {id: {userId}})
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      OPTIONAL MATCH (user)-[meta:META_SCORED]->(anime)
      RETURN anime.id as id, anime.name as name, meta.value as metascore, rating.score as score
      ORDER BY name
    `, {
      staffId,
      userId
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
          score: r.get('score'),
          metascore: r.get('metascore')
        }
      })
      resolve(r);
    })
    .catch((err) => {
      reject(err);
    })
  });
};

module.exports = {
  findById,
  findByUser,
  findByStaff
}
