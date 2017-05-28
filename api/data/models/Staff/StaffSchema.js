const winston = require('winston');

const findByUser = (server, userId, limit) => {
  winston.debug(`staff.findByUser ${userId}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH (user:User {id: {userId}})-[meta:META_SCORED]->(staff:Staff)
      WITH
        staff.id as id,
        staff.name as name,
        meta.value as metascore
      RETURN id, name, metascore
      ORDER BY metascore
      DESC LIMIT {limit}
    `, {
      userId,
      limit
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
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


const findByAnime = (server, animeId, userId) => {
  winston.debug('staff.findByAnime');
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH
        (:Anime {id: {animeId}})<-[:FOR]-(job:Job)<-[:HAS_JOB]-(staff:Staff),
        (job)-[:HAS]->(position:Position)
      OPTIONAL MATCH
        (user:User {id: {userId}})-[meta:META_SCORED]->(staff)
      WITH
        staff.id as id,
        staff.name as name,
        meta.value as metascore,
        COLLECT(position.name) as position
      RETURN id, name, metascore, position
      ORDER BY name
    `, {
      animeId,
      userId
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
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

const findById = (server, staffId, userId) => {
  winston.debug('staff.findById');
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH
        (staff:Staff {id: {staffId}})-[:HAS_JOB]->(:Job)-[:HAS]->(position:Position)
      OPTIONAL MATCH
        (user:User {id: {userId}})-[meta:META_SCORED]->(staff)
      WITH
        staff.id as id,
        staff.name as name,
        meta.value as metascore,
        collect(distinct position.name) as position
      RETURN id, name, metascore
      ORDER BY metascore
    `, {
      staffId,
      userId
    })
    .then(({ records }) => {
      const r = records.map(record => ({
        id: record.get('id'),
        name: record.get('name'),
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

module.exports = {
  findByUser,
  findById,
  findByAnime
};
