const findByUser = (server, userId, minCount, limit) => {
  console.log('staff.findByUser')
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
      minCount,
      limit
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
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

const findByAnime = (server, animeId, userId) => {
  console.log('staff.findByAnime')
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH
        (:Anime {id: {animeId}})<-[:WorkedOn]-(staff:Staff)
      OPTIONAL MATCH
        (user:User {id: {userId}})-[meta:META_SCORED]->(staff)
      WITH
        staff.id as id,
        staff.name as name,
        meta.value as metascore
      RETURN id, name, metascore
      ORDER BY name
    `, {
      animeId,
      userId
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
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

const findById = (server, staffId, userId) => {
  console.log('staff.findById')
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run(`
      MATCH
        (staff:Staff {id: {staffId}})
      OPTIONAL MATCH
        (user:User {id: {userId}})-[meta:META_SCORED]->(staff)
      WITH
        staff.id as id,
        staff.name as name,
        meta.value as metascore
      RETURN id, name, metascore
      ORDER BY metascore
    `, {
      staffId,
      userId
    })
    .then(({ records }) => {
      const r = records.map((r) => {
        return {
          id: r.get('id'),
          name: r.get('name'),
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

module.exports = {
  findByUser,
  findById,
  findByAnime
}
