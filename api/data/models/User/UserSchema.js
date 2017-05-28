const winston = require('winston');

const findById = (server, id) => {
  winston.debug(`user.findById ${id}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run('MATCH (user:User {id: toInteger({id})}) RETURN user.id as id, user.name as name', { id })
    .then(({ records }) => {
      session.close();
      const user = records.map(record => ({
        id: record.get('id').toNumber(),
        name: record.get('name')
      }));
      resolve(user[0]);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

const findByName = (server, name) => {
  winston.debug(`user.findByName ${name}`);
  return new Promise((resolve, reject) => {
    const session = server.session();
    session.run('MATCH (user:User {name: {name}}) RETURN user.id as id, user.name as name', { name })
    .then(({ records }) => {
      session.close();
      const user = records.map(record => ({
        id: record.get('id').toNumber(),
        name: record.get('name')
      }));
      resolve(user[0]);
    })
    .catch((err) => {
      reject(err);
    });
  });
};

module.exports = {
  findById,
  findByName
};
