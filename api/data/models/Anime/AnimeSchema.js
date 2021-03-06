const winston = require('winston');

const findByUser = (server, userId, limit) => {
  winston.debug(`anime.findByUser ${userId}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (user:User {id: {userId}})-[meta:META_SCORED]->(anime:Anime)
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      WITH
        anime.id as id,
        anime.name as name,
        meta.value as metascore,
        rating.score as score
      WHERE score > 0
      RETURN
        id,
        name,
        metascore,
        score
      ORDER BY metascore DESC
      LIMIT {limit}
    `, {
      userId,
      limit
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
        score: record.get('score'),
        metascore: record.get('metascore'),
        userId
      }));
      resolve(r);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

const findRecommendedByUser = (server, userId, limit) => {
  winston.debug(`anime.findByUser ${userId}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (user:User {id: {userId}})-[meta:META_SCORED]->(anime:Anime)
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      WITH
        anime.id as id,
        anime.name as name,
        meta.value as metascore,
        rating.score as score
      WHERE score is null OR score = 0
      RETURN
        id,
        name,
        metascore,
        score
      ORDER BY metascore DESC
      LIMIT {limit}
    `, {
      userId,
      limit
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
        score: record.get('score'),
        metascore: record.get('metascore'),
        userId
      }));
      resolve(r);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

const findById = (server, animeId, userId) => {
  winston.debug('anime.findById');
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
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
        score: record.get('score'),
        metascore: record.get('metascore'),
        userId
      }));
      resolve(r[0]);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

const findByStaff = (server, staffId, userId) => {
  winston.debug(`anime.findByStaff ${staffId} ${userId}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (:Staff {id: {staffId}})-[:HAS_JOB]->(job:Job)-[:FOR]->(anime:Anime),
        (job)-[:HAS]->(position:Position)
      MATCH (user:User {id: {userId}})
      OPTIONAL MATCH (user)-[rating:Rated]->(anime)
      OPTIONAL MATCH (user)-[meta:META_SCORED]->(anime)
      RETURN anime.id as id, anime.name as name, meta.value as metascore, rating.score as score, collect(position.name) as position
      ORDER BY name
    `, {
      staffId,
      userId
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
        score: record.get('score'),
        metascore: record.get('metascore'),
        position: record.get('position'),
        userId
      }));
      resolve(r);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

module.exports = {
  findById,
  findRecommendedByUser,
  findByUser,
  findByStaff
};
